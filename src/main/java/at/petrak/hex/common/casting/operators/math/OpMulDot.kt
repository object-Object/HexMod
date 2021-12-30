package at.petrak.hex.common.casting.operators.math

import at.petrak.hex.api.ConstManaOperator
import at.petrak.hex.api.SpellOperator.Companion.spellListOf
import at.petrak.hex.common.casting.CastingContext
import at.petrak.hex.common.casting.SpellDatum

object OpMulDot : ConstManaOperator {
    override val argc: Int
        get() = 2

    override fun execute(args: List<SpellDatum<*>>, ctx: CastingContext): List<SpellDatum<*>> {
        val lhs = MathOpUtils.GetNumOrVec(args[0])
        val rhs = MathOpUtils.GetNumOrVec(args[1])

        return spellListOf(
            lhs.map({ lnum ->
                rhs.map(
                    { rnum -> lnum * rnum }, { rvec -> rvec.scale(lnum) }
                )
            }, { lvec ->
                rhs.map(
                    { rnum -> lvec.multiply(rnum, rnum, rnum) }, { rvec -> lvec.dot(rvec) }
                )
            })
        )
    }
}