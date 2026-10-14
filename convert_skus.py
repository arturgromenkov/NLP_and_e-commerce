"""
Скрипт конвертации skus.pkl → skus.parquet
Запускать через терминал (НЕ через VS Code!):
    python convert_skus.py
"""
import pickle
import pandas as pd
import os


input_path = 'data/raw/skus.pkl'
output_path = 'data/raw/skus.parquet'

size_mb = os.path.getsize(input_path) / (1024 * 1024)
print(f" Размер pkl: {size_mb:.2f} MB")
print(f" Ожидаемый размер parquet: ~{size_mb * 0.3:.2f} MB")
print()

print(" Загружаю pickle (может занять время)...")
with open(input_path, 'rb') as f:
    df = pickle.load(f)

print(f" Загружено! Shape: {df.shape}")
print(f" Колонки: {df.columns.tolist()}")
print()

print(" Сохраняю в parquet...")
df.to_parquet(output_path, index=False, compression='snappy')

new_size_mb = os.path.getsize(output_path) / (1024 * 1024)
print(f" Готово! Новый размер: {new_size_mb:.2f} MB")
print(f" Сжатие: {size_mb / new_size_mb:.1f}x")
print()
print("Теперь в EDA используй: pd.read_parquet('data/raw/skus.parquet')")