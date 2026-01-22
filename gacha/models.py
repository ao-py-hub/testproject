from decimal import Decimal
import secrets
import string

from django.conf import settings
from django.db import models
from django.utils import timezone


def generate_public_id(length: int = 10) -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


class Gacha(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="gachas",
    )
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    public_id = models.CharField(
        max_length=16,
        unique=True,
        db_index=True,
        default=generate_public_id,
    )
    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self) -> str:
        return f"{self.title} ({self.public_id})"


class Prize(models.Model):
    gacha = models.ForeignKey(
        Gacha,
        on_delete=models.CASCADE,
        related_name="prizes",
    )
    name = models.CharField(max_length=80)

    # 小数点%対応（例: 12.5% / 0.25% / 33.33%）
    # max_digits=6, decimal_places=2 なら 100.00 まで扱える
    weight = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="確率(%)。小数点OK。削除を除いた合計が100.00になるように設定。",
    )

    stock_remaining = models.PositiveIntegerField(default=0)  # 排出残数
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self) -> str:
        return f"{self.name} / p={self.weight}% / left={self.stock_remaining}"
