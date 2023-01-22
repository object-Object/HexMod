package at.petrak.hexcasting.common.casting.operators.rw

import at.petrak.hexcasting.api.spell.ConstMediaAction
import at.petrak.hexcasting.api.spell.asActionResult
import at.petrak.hexcasting.api.spell.casting.CastingContext
import at.petrak.hexcasting.api.spell.iota.Iota
import at.petrak.hexcasting.api.spell.iota.NullIota
import at.petrak.hexcasting.xplat.IXplatAbstractions

object OpWritable : ConstMediaAction {
    override val argc = 0

    override fun execute(args: List<Iota>, ctx: CastingContext): List<Iota> {
        val (handStack) = ctx.getHeldItemToOperateOn {
            val datumHolder = IXplatAbstractions.INSTANCE.findDataHolder(it)

            datumHolder != null
        }

        val datumHolder = IXplatAbstractions.INSTANCE.findDataHolder(handStack) ?: return false.asActionResult
        val success = datumHolder.writeIota(NullIota(), true)
        return success.asActionResult
    }
}
