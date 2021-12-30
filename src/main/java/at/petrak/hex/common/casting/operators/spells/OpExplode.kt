package at.petrak.hex.common.casting.operators.spells

import at.petrak.hex.api.SimpleOperator
import at.petrak.hex.api.SpellOperator.Companion.getChecked
import at.petrak.hex.api.SpellOperator.Companion.spellListOf
import at.petrak.hex.common.casting.CastingContext
import at.petrak.hex.common.casting.RenderedSpell
import at.petrak.hex.common.casting.RenderedSpellImpl
import at.petrak.hex.common.casting.SpellDatum
import net.minecraft.util.Mth
import net.minecraft.world.level.Explosion
import net.minecraft.world.phys.Vec3

object OpExplode : SimpleOperator, RenderedSpellImpl {
    override val argc: Int
        get() = 2

    override fun execute(args: List<SpellDatum<*>>, ctx: CastingContext): Pair<List<SpellDatum<*>>, Int> {
        val pos = args.getChecked<Vec3>(0)
        val strength = args.getChecked<Double>(1)
        ctx.assertVecInRange(pos)
        return Pair(
            spellListOf(RenderedSpell(OpExplode, spellListOf(pos, strength))),
            (strength * 100.0).toInt(),
        )
    }

    override fun cast(args: List<SpellDatum<*>>, ctx: CastingContext) {
        val pos = args.getChecked<Vec3>(0)
        val strength = args.getChecked<Double>(1)

        ctx.world.explode(
            ctx.caster,
            pos.x,
            pos.y,
            pos.z,
            Mth.clamp(strength.toFloat(), 0f, 10f),
            Explosion.BlockInteraction.BREAK
        )
    }
}