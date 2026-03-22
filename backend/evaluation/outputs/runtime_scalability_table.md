Dataset | Model | Training Time (s) | Inference Time (ms/batch) | Peak Memory (MB)
---|---|---:|---:|---:
Small (10k) | ARIMA | 1.087 | 2.787 | 180.68
Small (10k) | Additive(ETS) | 1.105 | 73.540 | 167.54
Small (10k) | SARIMA | 27.786 | 4.335 | 873.17
Small (10k) | XGBoost | 0.251 | 57.882 | 276.70
Medium (50k) | ARIMA | 6.019 | 3.107 | 352.46
Medium (50k) | Additive(ETS) | 7.443 | 445.817 | 120.97
Medium (50k) | SARIMA | 173.056 | 5.991 | 3746.87
Medium (50k) | XGBoost | 0.528 | 101.481 | 191.24
Large (100k) | ARIMA | 16.221 | 4.465 | 363.43
Large (100k) | Additive(ETS) | 16.692 | 834.853 | 36.89
Large (100k) | SARIMA | 287.382 | 14.073 | 7120.79
Large (100k) | XGBoost | 0.477 | 51.984 | 65.94