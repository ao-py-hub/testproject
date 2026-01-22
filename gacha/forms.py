from django import forms
from django.forms import inlineformset_factory, BaseInlineFormSet
from .models import Gacha, Prize


class GachaForm(forms.ModelForm):
    class Meta:
        model = Gacha
        fields = ("title", "description", "is_public")

class PrizeForm(forms.ModelForm):
    class Meta:
        model = Prize
        fields = ("name", "weight", "stock_remaining", "sort_order")
        widgets = {
            "weight": forms.NumberInput(attrs={
                "min": 0,
                "max": 100,
                "step": "0.01",   # ★これが無いと小数は無効
            }),
            "stock_remaining": forms.NumberInput(attrs={
                "min": 0,
                "step": 1,
            }),
            "sort_order": forms.NumberInput(attrs={
                "min": 0,
                "step": 1,
            }),
        }
class BasePrizeFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()

        total = 0
        for form in self.forms:
            if not hasattr(form, "cleaned_data"):
                continue
            if form.cleaned_data.get("DELETE"):
                continue

            weight = form.cleaned_data.get("weight") or 0
            total += weight

        if total != 100:
            raise forms.ValidationError(
                f"確率の合計は100%である必要があります（現在：{total}%）"
            )


PrizeFormSet = inlineformset_factory(
    parent_model=Gacha,
    model=Prize,
    form=PrizeForm,
    formset=BasePrizeFormSet,
    extra=20,
    can_delete=True,
)
