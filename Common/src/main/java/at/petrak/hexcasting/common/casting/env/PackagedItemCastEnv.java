package at.petrak.hexcasting.common.casting.env;

import at.petrak.hexcasting.api.casting.eval.CastResult;
import at.petrak.hexcasting.api.casting.eval.sideeffects.EvalSound;
import at.petrak.hexcasting.api.casting.eval.sideeffects.OperatorSideEffect;
import at.petrak.hexcasting.api.misc.FrozenColorizer;
import at.petrak.hexcasting.common.lib.hex.HexEvalSounds;
import at.petrak.hexcasting.xplat.IXplatAbstractions;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;

public class PackagedItemCastEnv extends PlayerBasedCastEnv {

    protected EvalSound sound = HexEvalSounds.NOTHING;

    public PackagedItemCastEnv(ServerPlayer caster, InteractionHand castingHand) {
        super(caster, castingHand);
    }

    public EvalSound getFinalSound() {
        return sound;
    }

    @Override
    public void postExecution(CastResult result) {
        this.sound = this.sound.greaterOf(result.getSound());

        for (var sideEffect : result.getSideEffects()) {
            if (sideEffect instanceof OperatorSideEffect.DoMishap doMishap) {
                this.sendMishapMsgToPlayer(doMishap);
            }
        }
    }

    @Override
    public long extractMedia(long costLeft) {
        var casterStack = this.caster.getItemInHand(this.castingHand);
        var casterHexHolder = IXplatAbstractions.INSTANCE.findHexHolder(casterStack);
        var canCastFromInv = casterHexHolder.canDrawMediaFromInventory();

        var casterMediaHolder = IXplatAbstractions.INSTANCE.findMediaHolder(casterStack);

        // The contracts on the AD and on this function are different.
        // ADs return the amount extracted, this wants the amount left
        if (casterMediaHolder != null) {
            long extracted = casterMediaHolder.withdrawMedia((int) costLeft, false);
            costLeft -= extracted;
        }
        if (canCastFromInv && costLeft > 0) {
            costLeft = this.extractMediaFromInventory(costLeft, this.canOvercast());
        }

        return costLeft;
    }

    @Override
    public InteractionHand castingHand() {
        return this.castingHand;
    }

    @Override
    public FrozenColorizer getColorizer() {
        return null;
    }
}
