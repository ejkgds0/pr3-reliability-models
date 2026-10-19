import math
from typing import List, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


# Модель Джелински-Моранды
class JelinskiMorandaModel:
    def __init__(self, N0: int, phi: float):
        self.N0 = N0
        self.phi = phi

    def failure_intensity(self, i: int) -> float:
        # интенсивность отказов после исправления i ошибок
        remaining = self.N0 - i
        if remaining < 0:
            raise ValueError("Число исправленных ошибок не может превышать начальное")
        return self.phi * remaining

    def reliability(self, t: float, i: int = 0) -> float:
        # вероятность безотказной работы за время t
        lam = self.failure_intensity(i)
        return math.exp(-lam * t)

    def mttf(self, i: int = 0) -> float:
        # средняя наработка до отказа
        lam = self.failure_intensity(i)
        return 1.0 / lam if lam > 0 else float("inf")

    
# Модель Шумана
class SchumanModel:
    def __init__(self, I: int, E0: int, Ks: float):
        self.I = I
        self.E0 = E0
        self.Ks = Ks

    def residual_error_density(self, Ec: int) -> float:
        # удельное число остаточных ошибок
        return (self.E0 - Ec) / self.I

    def failure_intensity(self, Ec: int) -> float:
        return self.Ks * self.residual_error_density(Ec)

    def reliability(self, t: float, Ec: int = 0) -> float:
        lam = self.failure_intensity(Ec)
        return math.exp(-lam * t)

    def mttf(self, Ec: int = 0) -> float:
        lam = self.failure_intensity(Ec)
        return 1.0 / lam if lam > 0 else float("inf")

    @classmethod
    def estimate_parameters(cls, I, t1, t2, n1, n2, Ec1, Ec2) -> Tuple[float, float]:
        # оценка параметров E0 и Ks методом моментов
        gamma = (t1 * n2) / (t2 * n1) if n1 > 0 else 1.0
        E0 = I * (gamma * Ec1 - Ec2) / (gamma - 1) if gamma != 1 else 0
        Ks = n1 / (t1 * (E0 / I - Ec1 / I)) if (E0 / I - Ec1 / I) != 0 else 0
        return E0, Ks


# Объединённая модель Нельсона-Коркорэна
class NelsonCorcoranModel:
    def __init__(self, P: List[float], n: List[int], N: List[int],
                 N0: int = None, Ni: List[int] = None, ai: List[float] = None):
        if abs(sum(P) - 1.0) > 1e-6:
            raise ValueError("Сумма вероятностей P должна быть равна 1")
        if len(P) != len(n) or len(P) != len(N):
            raise ValueError("Длины списков P, n, N должны совпадать")
        self.P = P
        self.n = n
        self.N = N
        self.N0 = N0 if N0 is not None else sum(N) - sum(n)
        self.Ni = Ni
        self.ai = ai if ai else ([0.5] * len(Ni) if Ni else [])

    def reliability_nelson(self) -> float:
        # надёжность по части Нельсона (через подобласти)
        failure_prob = sum((ni / Ni) * Pi for ni, Ni, Pi in zip(self.n, self.N, self.P))
        return 1.0 - failure_prob

    def reliability_corcoran(self) -> float:
        # надёжность по расширению Коркорэна (учёт типов ошибок)
        if not self.Ni:
            return self.reliability_simple()
        K = len(self.Ni)
        sum_term = sum(self.ai[i] * (self.Ni[i] - 1) for i in range(K) if self.Ni[i] > 0)
        N_total = self.N0 + sum(self.Ni)
        return (self.N0 + sum_term) / N_total

    def reliability_simple(self) -> float:
        # упрощённая форма: 1 - n-/n
        n_failures = sum(self.n)
        n_total = sum(self.N)
        return 1.0 - n_failures / n_total

    def reliability(self) -> float:
        return self.reliability_nelson()

def demo_calculations():
    print("Расчет надежности")
    print("\n1. Модель Джелински-Моранды")
    jm = JelinskiMorandaModel(N0=50, phi=0.0001)
    print(f"  Интенсивность отказов (i=30): {jm.failure_intensity(30):.6f} отказов/час")
    print(f"  R(t=100) = {jm.reliability(100, i=30):.4f}")
    print(f"  MTTF = {jm.mttf(i=30):.2f} часов")

    print("\n2. Модель Шумана")
    sch = SchumanModel(I=10000, E0=50, Ks=0.0001)
    print(f"  Удельное число остаточных ошибок: {sch.residual_error_density(30):.6f}")
    print(f"  Интенсивность отказов: {sch.failure_intensity(30):.8f}")
    print(f"  R(t=100) = {sch.reliability(100, Ec=30):.8f}")
    print(f"  MTTF = {sch.mttf(Ec=30):.0f} часов")

    print("\n3. Модель Нельсона-Коркорэна")
    nc = NelsonCorcoranModel(P=[0.6, 0.4], n=[5, 2], N=[100, 50],
                              N0=970, Ni=[20, 10], ai=[0.7, 0.3])
    print(f"  R (Нельсон, через подобласти) = {nc.reliability_nelson():.4f}")
    print(f"  R (Коркорэн, с типами ошибок) = {nc.reliability_corcoran():.4f}")
    print(f"  R (упрощённая) = {nc.reliability_simple():.4f}")


def plot_reliability_curves():
    t = np.linspace(1, 500, 100)

    jm = JelinskiMorandaModel(N0=50, phi=0.0001)
    R_jm = [jm.reliability(ti, i=30) for ti in t]

    sch = SchumanModel(I=10000, E0=50, Ks=0.0001)
    R_sch = [sch.reliability(ti, Ec=30) for ti in t]

    plt.figure(figsize=(10, 6))
    plt.plot(t, R_jm, "b-", label="Джелински-Моранды", linewidth=2)
    plt.plot(t, R_sch, "r--", label="Шумана", linewidth=2)
    plt.axhline(y=0.95, color="gray", linestyle=":", label="Целевой уровень R=0.95")
    plt.xlabel("Время наработки, часы")
    plt.ylabel("Вероятность безотказной работы R(t)")
    plt.title("Сравнение моделей надёжности ПО")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig("reliability_curves.png", dpi=150)
    print("График сохранён: reliability_curves.png")


if __name__ == "__main__":
    demo_calculations()
    plot_reliability_curves()
