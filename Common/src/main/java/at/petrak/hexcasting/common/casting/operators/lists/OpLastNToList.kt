package at.petrak.hexcasting.common.casting.operators.lists

import at.petrak.hexcasting.api.casting.asActionResult
import at.petrak.hexcasting.api.casting.castables.Action
import at.petrak.hexcasting.api.casting.eval.CastingEnvironment
import at.petrak.hexcasting.api.casting.eval.OperationResult
import at.petrak.hexcasting.api.casting.eval.vm.SpellContinuation
import at.petrak.hexcasting.api.casting.getPositiveIntUnderInclusive
import at.petrak.hexcasting.api.casting.iota.Iota
import at.petrak.hexcasting.api.casting.mishaps.MishapNotEnoughArgs
import net.minecraft.nbt.CompoundTag

object OpLastNToList : Action {
    override fun operate(
        env: CastingEnvironment,
        stack: MutableList<Iota>,
        userData: CompoundTag,
        continuation: SpellContinuation
    ): OperationResult {
        if (stack.isEmpty())
            throw MishapNotEnoughArgs(1, 0)
        val yoinkCount = stack.takeLast(1).getPositiveIntUnderInclusive(0, stack.size - 1)
        stack.removeLast()
        val output = mutableListOf<Iota>()
        output.addAll(stack.takeLast(yoinkCount))
        for (i in 0 until yoinkCount) {
            stack.removeLast()
        }
        stack.addAll(output.asActionResult)

        return OperationResult(stack, userData, listOf(), continuation)
    }
}
