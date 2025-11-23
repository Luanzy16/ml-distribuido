import matplotlib.pyplot as plt
import io, base64

def plot_predictions(y_true, y_pred):
    plt.figure()
    plt.plot(y_true, label="True")
    plt.plot(y_pred, label="Predicted")
    plt.legend()
    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    img_bytes = buf.getvalue()
    buf.close()
    return base64.b64encode(img_bytes).decode("utf-8")
