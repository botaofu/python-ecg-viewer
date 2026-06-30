# Python ECG Viewer

一个轻量、易上手的桌面 ECG 查看器。它使用：

- `pandas` 读取 CSV 数据；
- `Matplotlib` 绘制可缩放、可平移的 ECG 波形；
- `PyQt6` 提供桌面窗口。

> 本项目只用于数据可视化，不提供医疗诊断或临床建议。

## 当前电脑直接运行

项目环境已经配置好。在项目目录打开终端，运行：

```bash
.venv/bin/python -m ecg_viewer
```

窗口打开后：

1. 点击 **Open CSV**。
2. 选择项目中的 `data/sample_ecg.csv`。
3. 在左侧 **Channel** 下拉框切换 `Lead I` 或 `Lead II`。
4. 使用图表工具栏中的 Pan、Zoom 和 Save。
5. 点击 **Reset View** 恢复完整波形范围。

## 在另一台电脑安装

需要 Python 3.10 或更高版本。

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
python -m ecg_viewer
```

Windows 激活虚拟环境时使用：

```powershell
.venv\Scripts\activate
```

## CSV 格式

CSV 至少需要一个数值型 ECG 通道，例如：

```csv
time,Lead I,Lead II
0.00,0.12,0.18
0.01,0.15,0.23
0.02,0.10,0.16
```

读取规则：

- 名为 `time`、`timestamp`、`seconds`、`second` 或 `t` 的数值列会被自动识别为时间轴；
- 时间列必须没有缺失值，并且严格递增；
- 没有合法时间列时，程序会弹窗要求输入采样率（Hz）；
- 其余数值列会显示为可选择的 ECG 通道；
- 文本元数据列会被忽略；
- ECG 缺失值会显示成波形断点，并在状态栏中提示数量。

## 运行测试

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -v
```

## 常见问题

- **窗口没有打开**：确认运行的是 `.venv/bin/python`，而不是系统自带的旧版 Python。
- **CSV 被拒绝**：确认文件用逗号分隔，并至少包含一个数值 ECG 列。
- **程序要求采样率**：说明 CSV 没有可识别的时间列；输入设备实际采样率即可。
- **波形有断点**：对应位置存在空值，程序会保留断点而不是擅自插值。
