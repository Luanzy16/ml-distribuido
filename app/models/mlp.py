import numpy as np

class MLP:
    def __init__(self, input_size, hidden_size=10, output_size=1, lr=0.01, n_iter=1000):
        self.lr = lr
        self.n_iter = n_iter
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.output_size = output_size
        self.W1 = np.random.randn(input_size, hidden_size) * 0.01
        self.b1 = np.zeros(hidden_size)
        self.W2 = np.random.randn(hidden_size, output_size) * 0.01
        self.b2 = np.zeros(output_size)

    def sigmoid(self, z):
        return 1 / (1 + np.exp(-z))

    def sigmoid_derivative(self, z):
        return z * (1 - z)

    def fit(self, X, y):
        for _ in range(self.n_iter):
            # Forward
            z1 = np.dot(X, self.W1) + self.b1
            a1 = self.sigmoid(z1)
            z2 = np.dot(a1, self.W2) + self.b2
            a2 = self.sigmoid(z2)

            # Backprop
            dz2 = a2 - y.reshape(-1,1)
            dW2 = np.dot(a1.T, dz2)
            db2 = np.sum(dz2, axis=0)
            dz1 = np.dot(dz2, self.W2.T) * self.sigmoid_derivative(a1)
            dW1 = np.dot(X.T, dz1)
            db1 = np.sum(dz1, axis=0)

            # Update
            self.W1 -= self.lr * dW1
            self.b1 -= self.lr * db1
            self.W2 -= self.lr * dW2
            self.b2 -= self.lr * db2

    def predict(self, X):
        z1 = np.dot(X, self.W1) + self.b1
        a1 = self.sigmoid(z1)
        z2 = np.dot(a1, self.W2) + self.b2
        a2 = self.sigmoid(z2)
        return (a2 >= 0.5).astype(int)
