import numpy as np

class ARIMA:
    def __init__(self, order=(1, 0, 0)):
        """
        ARIMA 模型初始化
        :param order: (p, d, q) 分别表示 AR、差分、MA 的阶数
        """
        self.p, self.d, self.q = order
        self.ar_coefs = None  # AR 系数
        self.ma_coefs = None  # MA 系数
        self.residuals = []  # 残差（用于 MA 部分）
        self.mean = 0  # 数据均值（用于标准化）
        self.std = 1  # 数据标准差（用于标准化）

    def fit(self, data):
        """拟合 ARIMA 模型"""
        if len(data) < max(self.p, self.q) + 1:
            raise ValueError("Not enough data to fit ARIMA model")

        # 数据标准化
        self.mean = np.mean(data)
        self.std = np.std(data)
        if self.std == 0:
            self.std = 1  # 避免除零错误
        normalized_data = (data - self.mean) / self.std

        # 差分处理
        diff_data = self._difference(normalized_data, self.d)

        # 拟合 AR 部分
        if self.p > 0:
            self.ar_coefs = self._fit_ar(diff_data, self.p)

        # 计算残差（用于 MA 部分）
        self.residuals = self._calculate_residuals(diff_data, self.ar_coefs)

        # 拟合 MA 部分
        if self.q > 0:
            self.ma_coefs = self._fit_ma(self.residuals, self.q)

    def forecast(self, steps=1):
        """预测未来值"""
        if not self.ar_coefs and not self.ma_coefs:
            raise ValueError("Model not fitted yet")

        predictions = []
        for _ in range(steps):
            # AR 部分预测
            ar_value = 0
            if self.p > 0:
                ar_value = np.dot(self.ar_coefs, [self.residuals[-i] for i in range(1, self.p + 1)][::-1])

            # MA 部分预测
            ma_value = 0
            if self.q > 0:
                ma_value = np.dot(self.ma_coefs, [self.residuals[-i] for i in range(1, self.q + 1)][::-1])

            # 综合预测值
            pred = ar_value + ma_value
            predictions.append(pred)

            # 更新残差
            self.residuals.append(pred)

        # 反标准化
        predictions = np.array(predictions) * self.std + self.mean
        return predictions.tolist()

    def _difference(self, data, d):
        """差分处理"""
        for _ in range(d):
            data = np.diff(data)
        return data

    def _fit_ar(self, data, p):
        """拟合 AR 部分"""
        if p == 0:
            return []

        # 构建自回归矩阵
        X = np.zeros((len(data) - p, p))
        for i in range(p, len(data)):
            X[i - p] = data[i - p:i]

        # 目标值
        y = data[p:]

        # 最小二乘法求解 AR 系数
        ar_coefs = np.linalg.lstsq(X, y, rcond=None)[0]
        return ar_coefs

    def _calculate_residuals(self, data, ar_coefs):
        """计算残差"""
        residuals = []
        for i in range(len(ar_coefs), len(data)):
            pred = np.dot(ar_coefs, data[i - len(ar_coefs):i])
            residuals.append(data[i] - pred)
        return residuals

    def _fit_ma(self, residuals, q):
        """拟合 MA 部分"""
        if q == 0:
            return []

        # 构建移动平均矩阵
        X = np.zeros((len(residuals) - q, q))
        for i in range(q, len(residuals)):
            X[i - q] = residuals[i - q:i]

        # 目标值
        y = residuals[q:]

        # 最小二乘法求解 MA 系数
        ma_coefs = np.linalg.lstsq(X, y, rcond=None)[0]
        return ma_coefs