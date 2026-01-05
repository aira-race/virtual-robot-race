# Training Info - iteration_260104_204326

**Created:** 2026-01-04 20:50:06

## データソース

### 使用したrun
- run_20260104_203717
- run_20260104_203812
- run_20260104_203901

（合計: 3 runs, 1,273 フレーム）

### データ統計
- 総フレーム数: 1,273
- Training: 1,019 (80.0%)
- Validation: 254 (20.0%)

## モデルアーキテクチャ

```
DrivingNetwork(
  (cnn): Sequential(
    (0): Conv2d(3, 32, kernel_size=(5, 5), stride=(2, 2), padding=(2, 2))
    (1): BatchNorm2d(32, eps=1e-05, momentum=0.1, affine=True, track_running_stats=True)
    (2): ReLU(inplace=True)
    (3): Conv2d(32, 64, kernel_size=(5, 5), stride=(2, 2), padding=(2, 2))
    (4): BatchNorm2d(64, eps=1e-05, momentum=0.1, affine=True, track_running_stats=True)
    (5): ReLU(inplace=True)
    (6): Conv2d(64, 128, kernel_size=(5, 5), stride=(2, 2), padding=(2, 2))
    (7): BatchNorm2d(128, eps=1e-05, momentum=0.1, affine=True, track_running_stats=True)
    (8): ReLU(inplace=True)
    (9): Conv2d(128, 256, kernel_size=(5, 5), stride=(2, 2), padding=(2, 2))
    (10): BatchNorm2d(256, eps=1e-05, momentum=0.1, affine=True, track_running_stats=True)
    (11): ReLU(inplace=True)
    (12): AdaptiveAvgPool2d(output_size=(1, 1))
  )
  (mlp): Sequential(
    (0): Linear(in_features=257, out_features=128, bias=True)
    (1): ReLU(inplace=True)
    (2): Dropout(p=0.3, inplace=False)
    (3): Linear(in_features=128, out_features=64, bias=True)
    (4): ReLU(inplace=True)
    (5): Dropout(p=0.2, inplace=False)
    (6): Linear(in_features=64, out_features=2, bias=True)
  )
)
```

### パラメータ数
- Total parameters: 1,120,450
- Trainable parameters: 1,120,450
- Model size: 4.27 MB (FP32)

## 学習設定

- **エポック数:** 50
- **バッチサイズ:** 32
- **学習率:** 0.0001
- **Optimizer:** AdamW (weight_decay=1e-4)
- **Loss Function:** MSE
- **Scheduler:** ReduceLROnPlateau (factor=0.5, patience=10)
- **Device:** cuda
- **Train/Val Split:** 80/20

## 学習結果

- **最終Train Loss:** 0.086824
- **最終Val Loss:** 0.075478
- **最良Val Loss:** 0.068462 (epoch 46)
- **学習時間:** 0h 3m 33s
- **過学習チェック:** Val/Train比 = 0.869 ✅ 正常

### Loss詳細（最終エポック）

| 指標 | Train | Val |
|-----|-------|-----|
| Total Loss | 0.086824 | 0.075478 |

### Loss推移グラフ

![Loss Curve](logs/loss_curve.png)

## 評価結果（3回走行）

| Run | 完走 | 時間(s) | クラッシュ地点 | 原因 |
|-----|------|---------|--------------|------|
| 1   | ❌   | 14.2    | pos_x=3.11   | スタート直後に右ステア→右壁衝突 |
| 2   | ❌   | 14.1    | pos_x=3.11   | スタート直後に右ステア→右壁衝突 |
| 3   | ❌   | 14.3    | pos_x=3.11   | スタート直後に右ステア→右壁衝突 |

**完走率:** 0% (0/3)
**平均走行時間:** 14.2秒（全てクラッシュ）

### 失敗原因分析

1. **学習データの右ステアリングバイアス**
   - 平均ステア: +0.29 rad（右）
   - 右:左:ニュートラル = 57.7% : 0.2% : 42.1%
   - モデルは「基本的に右に切る」ことを学習

2. **コーナーデータの不足**
   - 学習データは直線中心
   - 急なコーナリングの例がない
   - 最初のコーナー（pos_x≈30）に到達できず

3. **3回とも同じ位置でクラッシュ**
   - pos_x ≈ 3.1（スタート直後）
   - システマティックな問題（ランダムではない）
   - モデルは正しく動作しているが、学習データが不適切

詳細: `evaluation/evaluation_summary.md`

## 次のステップ

1. ✅ 学習完了
2. ✅ テスト走行（3回）を実施
3. ✅ 完走率を評価
4. ✅ クラッシュ分析完了
5. ⏳ **次のiteration**: より良い学習データを収集

### 次回のiteration改善案

- [ ] バランスの取れたステアリングデータ（左右均等）
- [ ] コーナー走行を含むデータ
- [ ] データ拡張（水平反転）の活用
- [ ] 完走率 > 33% を目標

## 備考

**Iteration 1の結論:**
- モデルアーキテクチャは問題なし（1.12M params, Val/Train=0.869）
- 学習は正常に完了（過学習なし）
- **問題は学習データの質**（右バイアス、コーナー不足）
- 次回は手動走行時に左右バランスとコーナーを意識

---
**生成日時:** 2026-01-04T20:50:06.495752
