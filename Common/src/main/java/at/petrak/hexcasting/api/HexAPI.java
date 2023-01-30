package at.petrak.hexcasting.api;

import com.google.common.base.Suppliers;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.phys.Vec3;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

import java.util.function.Supplier;

public interface HexAPI {
    String MOD_ID = "hexcasting";
    Logger LOGGER = LogManager.getLogger(MOD_ID);

    Supplier<HexAPI> INSTANCE = Suppliers.memoize(() -> {
        try {
            return (HexAPI) Class.forName("at.petrak.hexcasting.common.impl.HexAPIImpl")
                .getDeclaredConstructor().newInstance();
        } catch (ReflectiveOperationException e) {
            LogManager.getLogger().warn("Unable to find HexAPIImpl, using a dummy");
            return new HexAPI() {
            };
        }
    });

    /**
     * Register an entity with the given ID to have its velocity as perceived by OpEntityVelocity be different
     * than it's "normal" velocity
     */
    // Should be OK to use the type directly as the key as they're singleton identity objects
    default <T extends Entity> void registerSpecialVelocityGetter(EntityType<T> key, EntityVelocityGetter<T> getter) {
    }

    /**
     * If the entity has had a special getter registered with {@link HexAPI#registerSpecialVelocityGetter} then
     * return that, otherwise return its normal delta movement
     */
    default Vec3 getEntityVelocitySpecial(Entity entity) {
        return entity.getDeltaMovement();
    }

    @FunctionalInterface
    interface EntityVelocityGetter<T extends Entity> {
        Vec3 getVelocity(T entity);
    }

    static HexAPI instance() {
        return INSTANCE.get();
    }

    static ResourceLocation modLoc(String s) {
        return new ResourceLocation(MOD_ID, s);
    }
}
