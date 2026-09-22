def get_signal_quality(rssi: int):
    rating = "Excellent" if rssi >= -50 else "Very Good" if rssi >= -60 else "Good" if rssi >= -67 else "Fair" if rssi >= -75 else "Weak"
    # Piecewise interpolation makes -58 approximately 82, without implying precision.
    anchors = [(-100, 0), (-75, 40), (-67, 60), (-60, 80), (-50, 90), (-30, 100)]
    quality = 0.0
    if rssi >= -30:
        quality = 100.0
    else:
        for (x0, y0), (x1, y1) in zip(anchors, anchors[1:]):
            if x0 <= rssi <= x1:
                quality = y0 + (rssi - x0) * (y1 - y0) / (x1 - x0)
                break
    return {"rssi": rssi, "quality": round(quality), "rating": rating}


def percentage_rating(percent: int):
    return "Excellent" if percent >= 90 else "Very Good" if percent >= 80 else "Good" if percent >= 60 else "Fair" if percent >= 40 else "Weak"
