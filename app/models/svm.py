import numpy as np

class SVM:
    def __init__(self, lr=0.001, n_iter=1000, C=1.0):
        self.lr = lr
        self.n_iter = n_iter
        self.C = C
        self.weights = None
        self.bias = None

    def fit(self, X, y):
        y_ = np.where(y <= 0, -1, 1)
        n_samples, n_features = X.shape
        self.weights = np.zeros(n_features)
        self.bias = 0

        for _ in range(self.n_iter):
            for idx, x_i in enumerate(X):
                condition = y_[idx] * (np.dot(x_i, self.weights) + self.bias) >= 1
                if condition:
                    self.weights -= self.lr * (2 * self.C * self.weights)
                else:
                    self.weights -= self.lr * (2 * self.C * self.weights - np.dot(x_i, y_[idx]))
                    self.bias -= self.lr * y_[idx]

    def predict(self, X):
        approx = np.dot(X, self.weights) + self.bias
        return np.sign(approx)
