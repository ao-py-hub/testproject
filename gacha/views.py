from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import F
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods
import random
from django.views.decorators.http import require_POST
from django.views.decorators.http import require_http_methods, require_POST

from .models import Gacha, Prize
from .forms import GachaForm, PrizeFormSet


def home(request):
    q = (request.GET.get("q") or "").strip()

    # 公開ガチャ一覧（最新順）
    public_gachas = (
        Gacha.objects
        .filter(is_public=True)
        .order_by("-created_at")
    )

    # ID検索（ヒットしたら上に出す）
    hit = None
    if q:
        hit = Gacha.objects.filter(public_id=q, is_public=True).first()

    # 自分のガチャ一覧（ログイン時のみ）
    my_gachas = None
    if request.user.is_authenticated:
        my_gachas = (
            Gacha.objects
            .filter(owner=request.user)
            .order_by("-created_at")
        )

    return render(request, "gacha/home.html", {
        "q": q,
        "hit": hit,
        "public_gachas": public_gachas,
        "my_gachas": my_gachas,
    })
@login_required
@require_http_methods(["GET", "POST"])
def gacha_create(request):
    if request.method == "POST":
        form = GachaForm(request.POST)
        if form.is_valid():
            g = form.save(commit=False)
            g.owner = request.user
            g.save()
            return redirect("gacha:manage", public_id=g.public_id)
    else:
        form = GachaForm()
    return render(request, "gacha/gacha_create.html", {"form": form})

@login_required
@require_http_methods(["GET", "POST"])
def manage(request, public_id):
    g = get_object_or_404(Gacha, public_id=public_id, owner=request.user)

    if request.method == "POST":
        form = GachaForm(request.POST, instance=g)
        formset = PrizeFormSet(request.POST, instance=g)  # ★必須（これがズレると壊れる）
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            return redirect("gacha:manage", public_id=g.public_id)
    else:
        form = GachaForm(instance=g)
        formset = PrizeFormSet(instance=g)

    return render(request, "gacha/gacha_manage.html", {"gacha": g, "form": form, "formset": formset})

def public_view(request, public_id):
    g = get_object_or_404(Gacha, public_id=public_id, is_public=True)
    prizes = g.prizes.all()
    return render(request, "gacha/gacha_public.html", {"gacha": g, "prizes": prizes})

@login_required
@require_http_methods(["GET", "POST"])
def draw(request, public_id):
    g = get_object_or_404(Gacha, public_id=public_id, is_public=True)

    if request.method == "GET":
        return render(request, "gacha/gacha_draw.html", {"gacha": g})

    with transaction.atomic():
        prizes = list(
            Prize.objects.select_for_update()
            .filter(gacha=g, stock_remaining__gt=0, weight__gt=0)
        )
        if not prizes:
            return render(request, "gacha/gacha_result.html", {"gacha": g, "sold_out": True})

        total = sum(p.weight for p in prizes)
        r = random.randint(1, total)
        upto = 0
        chosen = prizes[0]
        for p in prizes:
            upto += p.weight
            if r <= upto:
                chosen = p
                break

        Prize.objects.filter(pk=chosen.pk, stock_remaining__gt=0).update(stock_remaining=F("stock_remaining") - 1)
        chosen.refresh_from_db()

    return render(request, "gacha/gacha_result.html", {"gacha": g, "sold_out": False, "prize": chosen})
@login_required
@require_POST
def delete_gacha(request, public_id):
    gacha = get_object_or_404(
        Gacha,
        public_id=public_id,
        owner=request.user,   # 作成者のみ削除可
    )
    gacha.delete()
    return redirect("gacha:home")


def draw(request, public_id):
    gacha = get_object_or_404(Gacha, public_id=public_id, is_public=True)

    prizes = list(
        gacha.prizes.filter(
            stock_remaining__gt=0,
            weight__gt=0
        )
    )

    if not prizes:
        return render(request, "gacha/gacha_result.html", {
            "gacha": gacha,
            "sold_out": True,
        })

    # 1〜100 の乱数（％）
    r = random.randint(1, 100)

    cumulative = 0
    chosen = None
    for p in prizes:
        cumulative += p.weight
        if r <= cumulative:
            chosen = p
            break

    # 念のためフォールバック
    if chosen is None:
        chosen = prizes[-1]

    # 在庫減算（排他制御）
    with transaction.atomic():
        chosen.stock_remaining -= 1
        chosen.save(update_fields=["stock_remaining"])

    return render(request, "gacha/gacha_result.html", {
        "gacha": gacha,
        "prize": chosen,
        "sold_out": False,
    })