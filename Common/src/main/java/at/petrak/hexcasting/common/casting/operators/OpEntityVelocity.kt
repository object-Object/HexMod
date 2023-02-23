package at.petrak.hexcasting.common.casting.operators

import at.petrak.hexcasting.api.HexAPI
import at.petrak.hexcasting.api.casting.asActionResult
import at.petrak.hexcasting.api.casting.castables.ConstMediaAction
import at.petrak.hexcasting.api.casting.eval.CastingEnvironment
import at.petrak.hexcasting.api.casting.getEntity
import at.petrak.hexcasting.api.casting.iota.Iota

object OpEntityVelocity : ConstMediaAction {
    override val argc = 1

    override fun execute(args: List<Iota>, ctx: CastingEnvironment): List<Iota> {
        val e = args.getEntity(0, argc)
        ctx.assertEntityInRange(e)

        val vel = HexAPI.instance().getEntityVelocitySpecial(e)
        return vel.asActionResult
    }
}
