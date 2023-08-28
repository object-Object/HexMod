# pyright: reportInvalidTypeVarUse=information

import logging
import subprocess
from collections.abc import Iterator
from contextlib import ExitStack, contextmanager
from pathlib import Path
from typing import Callable, Literal, Self, TypeVar, overload

from pydantic.dataclasses import dataclass

from hexdoc.utils.deserialize import JSONDict, decode_json_dict
from hexdoc.utils.model import DEFAULT_CONFIG, HexdocModel, ValidationContext
from hexdoc.utils.types import strip_suffixes

from .properties import Properties
from .resource import PathResourceDir, ResourceLocation, ResourceType

METADATA_SUFFIX = ".hexdoc.json"

_T = TypeVar("_T")
_T_Model = TypeVar("_T_Model", bound=HexdocModel)

ExportFn = Callable[[_T, _T | None, Path], str | tuple[str, Path]]


class HexdocMetadata(HexdocModel):
    """Automatically generated at `export_dir/modid.hexdoc.json`."""

    book_url: str

    @classmethod
    def path(cls, modid: str) -> Path:
        return Path(f"{modid}.hexdoc.json")


@dataclass(config=DEFAULT_CONFIG, kw_only=True)
class ModResourceLoader:
    props: Properties
    resource_dirs: list[PathResourceDir]

    @classmethod
    @contextmanager
    def clean_and_load_all(cls, props: Properties) -> Iterator[Self]:
        # clear the export dir so we start with a clean slate
        if props.export_dir:
            subprocess.run(["git", "clean", "-fdX", props.export_dir])

        with ExitStack() as stack:
            loader = cls(
                props=props,
                resource_dirs=[
                    path_resource_dir
                    for resource_dir in props.resource_dirs
                    for path_resource_dir in stack.enter_context(resource_dir.load())
                ],
            )

            # export this mod's metadata
            loader.export(
                path=HexdocMetadata.path(props.modid),
                data=HexdocMetadata(
                    book_url=props.url,
                ).model_dump_json(),
            )

            yield loader

    def __post_init__(self):
        self.mod_metadata = self.load_metadata("{modid}", HexdocMetadata)

    def get_link_base(self, resource_dir: PathResourceDir) -> str:
        modid = resource_dir.modid
        if modid is None or modid == self.props.modid:
            return ""
        return self.mod_metadata[modid].book_url

    def load_metadata(
        self,
        name_pattern: str,
        model_type: type[_T_Model],
    ) -> dict[str, _T_Model]:
        """eg. `"{modid}.patterns"`"""
        metadata = dict[str, _T_Model]()

        for resource_dir in self.resource_dirs:
            # skip if we've already loaded this mod's metadata
            modid = resource_dir.modid
            if modid is None or modid in metadata:
                continue

            _, metadata[modid] = self.load_resource(
                Path(name_pattern.format(modid=modid) + METADATA_SUFFIX),
                decode=model_type.model_validate_json,
                export=False,
            )

        return metadata

    def load_book_assets(
        self, folder: Literal["categories", "entries", "templates"]
    ) -> Iterator[tuple[PathResourceDir, ResourceLocation, JSONDict]]:
        yield from self.load_resources(
            type="assets",
            folder=Path("patchouli_books")
            / self.props.book.path
            / self.props.default_lang
            / folder,
            namespace=self.props.book.namespace,
        )

    @overload
    def load_resource(
        self,
        type: ResourceType,
        folder: str | Path,
        id: ResourceLocation,
        *,
        decode: Callable[[str], _T] = decode_json_dict,
        export: ExportFn[_T] | Literal[False] | None = None,
    ) -> tuple[PathResourceDir, _T]:
        ...

    @overload
    def load_resource(
        self,
        path: Path,
        /,
        *,
        decode: Callable[[str], _T] = decode_json_dict,
        export: ExportFn[_T] | Literal[False] | None = None,
    ) -> tuple[PathResourceDir, _T]:
        ...

    def load_resource(
        self,
        type: ResourceType | Path,
        folder: str | Path | None = None,
        id: ResourceLocation | None = None,
        *,
        decode: Callable[[str], _T] = decode_json_dict,
        export: ExportFn[_T] | Literal[False] | None = None,
    ) -> tuple[PathResourceDir, _T]:
        """Find the first file with this resource location in `resource_dirs`.

        If no file extension is provided, `.json` is assumed.

        Raises FileNotFoundError if the file does not exist.
        """

        if isinstance(type, Path):
            path_stub = type
        else:
            assert folder is not None and id is not None
            path_stub = id.file_path_stub(type, folder)

        # check by descending priority, return the first that exists
        for resource_dir in self.resource_dirs:
            try:
                return resource_dir, self._load_path(
                    resource_dir,
                    resource_dir.path / path_stub,
                    decode=decode,
                    export=export,
                )
            except FileNotFoundError:
                continue

        raise FileNotFoundError(f"Path {path_stub} not found in any resource dir")

    @overload
    def load_resources(
        self,
        type: ResourceType,
        folder: str | Path,
        *,
        namespace: str,
        glob: str | list[str] = "**/*",
        decode: Callable[[str], _T] = decode_json_dict,
        export: ExportFn[_T] | Literal[False] | None = None,
    ) -> Iterator[tuple[PathResourceDir, ResourceLocation, _T]]:
        ...

    @overload
    def load_resources(
        self,
        type: ResourceType,
        folder: str | Path,
        id: ResourceLocation,
        *,
        decode: Callable[[str], _T] = decode_json_dict,
        export: ExportFn[_T] | Literal[False] | None = None,
    ) -> Iterator[tuple[PathResourceDir, ResourceLocation, _T]]:
        ...

    def load_resources(
        self,
        type: ResourceType,
        folder: str | Path,
        id: ResourceLocation | None = None,
        *,
        namespace: str | None = None,
        glob: str | list[str] = "**/*",
        decode: Callable[[str], _T] = decode_json_dict,
        export: ExportFn[_T] | Literal[False] | None = None,
    ) -> Iterator[tuple[PathResourceDir, ResourceLocation, _T]]:
        """Search for a glob under a given resource location in all of `resource_dirs`.

        Files are returned from lowest to highest priority in the load order, ie. later
        files should overwrite earlier ones.

        If no file extension is provided for glob, `.json` is assumed.

        Raises FileNotFoundError if no files were found in any resource dir.

        For example:
        ```py
        props.find_resources(
            "assets",
            "lang/subdir",
            namespace="*",
            glob="*.flatten.json5",
        )

        # [(hexcasting:en_us, .../resources/assets/hexcasting/lang/subdir/en_us.json)]
        ```
        """

        if id is not None:
            namespace = id.namespace
            glob = id.path

        # eg. assets/*/lang/subdir
        if namespace is not None:
            base_path_stub = Path(type) / namespace / folder
        else:
            raise RuntimeError(
                "No overload matches the specified arguments (expected id or namespace)"
            )

        # glob for json files if not provided
        globs = [glob] if isinstance(glob, str) else glob
        for i in range(len(globs)):
            if not Path(globs[i]).suffix:
                globs[i] += ".json"

        # find all files matching the resloc
        found_any = False
        for resource_dir in reversed(self.resource_dirs):
            # eg. .../resources/assets/*/lang/subdir
            for base_path in resource_dir.path.glob(base_path_stub.as_posix()):
                for glob_ in globs:
                    # eg. .../resources/assets/hexcasting/lang/subdir/*.flatten.json5
                    for path in base_path.glob(glob_):
                        id = ResourceLocation(
                            # eg. ["assets", "hexcasting", "lang", ...][1]
                            namespace=path.relative_to(resource_dir.path).parts[1],
                            path=strip_suffixes(path.relative_to(base_path)).as_posix(),
                        )

                        try:
                            value = self._load_path(
                                resource_dir,
                                path,
                                decode=decode,
                                export=export,
                            )
                            found_any = True
                            yield resource_dir, id, value
                        except FileNotFoundError:
                            continue

        # if we never yielded any files, raise an error
        if not found_any:
            raise FileNotFoundError(
                f"No files found under {base_path_stub}/{globs} in any resource dir"
            )

    def _load_path(
        self,
        resource_dir: PathResourceDir,
        path: Path,
        *,
        decode: Callable[[str], _T] = decode_json_dict,
        export: ExportFn[_T] | Literal[False] | None = None,
    ) -> _T:
        if not path.is_file():
            raise FileNotFoundError(path)

        logging.getLogger(__name__).info(f"Loading {path}")

        data = path.read_text("utf-8")
        value = decode(data)

        if resource_dir.reexport and export is not False:
            self.export(
                path.relative_to(resource_dir.path),
                data,
                value,
                decode=decode,
                export=export,
            )

        return value

    @overload
    def export(self, /, path: Path, data: str) -> None:
        ...

    @overload
    def export(
        self,
        /,
        path: Path,
        data: str,
        value: _T,
        *,
        decode: Callable[[str], _T] = decode_json_dict,
        export: ExportFn[_T] | None = None,
    ) -> None:
        ...

    def export(
        self,
        path: Path,
        data: str,
        value: _T = None,
        *,
        decode: Callable[[str], _T] = decode_json_dict,
        export: ExportFn[_T] | None = None,
    ) -> None:
        if not self.props.export_dir:
            return
        out_path = self.props.export_dir / path

        logging.getLogger(__name__).debug(f"Exporting {path} to {out_path}")
        if export is None:
            out_data = data
        else:
            try:
                old_value = decode(out_path.read_text("utf-8"))
            except FileNotFoundError:
                old_value = None

            match export(value, old_value, out_path):
                case str(out_data):
                    pass
                case (str(out_data), Path() as out_path):
                    pass

        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(out_data, "utf-8")


class LoaderContext(ValidationContext):
    loader: ModResourceLoader

    @property
    def props(self):
        return self.loader.props