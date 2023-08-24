import logging
from pathlib import Path
from typing import Self

from pydantic import Field, model_validator

from hexdoc.minecraft.tags import Tag
from hexdoc.patchouli.book import BookContext
from hexdoc.utils import ResourceLocation
from hexdoc.utils.model import HexDocModel
from hexdoc.utils.properties import PatternStubProps

from .pattern import Direction, PatternInfo


class PatternMetadata(HexDocModel):
    """Automatically generated at `export_dir/modid.patterns.hexdoc.json`."""

    patterns: dict[ResourceLocation, PatternInfo]

    @classmethod
    def path(cls, modid: str) -> Path:
        return Path(f"{modid}.patterns.hexdoc.json")


# conthext, perhaps
class HexContext(BookContext):
    patterns: dict[ResourceLocation, PatternInfo] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _post_root_load_patterns(self) -> Self:
        # load the tag that specifies which patterns are random per world
        per_world = Tag.load(
            registry="action",
            id=ResourceLocation("hexcasting", "per_world_pattern"),
            context=self,
        )

        signatures = dict[str, PatternInfo]()  # just for duplicate checking

        # for each stub, load all the patterns in the file
        for stub in self.props.pattern_stubs:
            for pattern in self._load_stub_patterns(stub, per_world):
                self._add_pattern(pattern, signatures)

        # export patterns so addons can use them
        self.loader.export(
            path=PatternMetadata.path(self.props.modid),
            data=PatternMetadata(
                patterns=self.patterns,
            ).model_dump_json(warnings=False),
        )

        # add external patterns AFTER exporting so we don't reexport them
        for metadata in self.loader.load_metadata(
            "{modid}.patterns", PatternMetadata
        ).values():
            for _, pattern in metadata.patterns.items():
                self._add_pattern(pattern, signatures)

        return self

    def _add_pattern(self, pattern: PatternInfo, signatures: dict[str, PatternInfo]):
        logging.getLogger(__name__).debug(f"Load pattern: {pattern.id}")

        # check for duplicates, because why not
        if duplicate := (
            self.patterns.get(pattern.id) or signatures.get(pattern.signature)
        ):
            raise ValueError(f"Duplicate pattern {pattern.id}\n{pattern}\n{duplicate}")

        self.patterns[pattern.id] = pattern
        signatures[pattern.signature] = pattern

    def _load_stub_patterns(self, stub: PatternStubProps, per_world: Tag):
        # TODO: add Gradle task to generate json with this data. this is dumb and fragile.
        stub_text = stub.path.read_text("utf-8")

        for match in stub.regex.finditer(stub_text):
            groups = match.groupdict()
            id = self.props.mod_loc(groups["name"])

            yield PatternInfo(
                startdir=Direction[groups["startdir"]],
                signature=groups["signature"],
                is_per_world=id in per_world.values,
                id=id,
            )
