---
name: Bug Report
about: Create a report to help us improve qtframeless
title: "[Bug] "
labels: ["bug"]
assignees: ""
---

### Description

<!-- A clear and concise description of what the bug is. -->

### Environment

| Property | Value |
| :--- | :--- |
| **qtframeless Version** | <!-- e.g. 0.1.0 --> |
| **Windows OS & Build** | <!-- e.g. Windows 11 23H2 Build 22631 / Windows 10 22H2 Build 19045 --> |
| **Qt Binding & Version** | <!-- e.g. PySide6 6.8.0 / PyQt6 6.7.0 / PyQt5 5.15.10 --> |
| **Python Version** | <!-- e.g. 3.11.9 --> |
| **Display Scaling / DPI** | <!-- e.g. 100% 96 DPI, 150% 144 DPI, multi-monitor --> |

### Window Configuration

<!-- Check all window classes applicable to this issue: -->
- [ ] `FramelessMainWindow`
- [ ] `FramelessWindow`
- [ ] `FramelessDialog`
- [ ] `FramelessWidget`
- [ ] `FramelessMicaMainWindow`
- [ ] `FramelessAcrylicMainWindow`

### Minimal Reproducible Example

<!-- Provide a minimal, self-contained Python script reproducing the issue. -->

```python
import sys
from PySide6.QtWidgets import QApplication
from qtframeless import FramelessMainWindow

app = QApplication(sys.argv)
window = FramelessMainWindow()
window.show()
sys.exit(app.exec())
```

### Expected Behavior

<!-- A clear and concise description of what you expected to happen. -->

### Screenshots / Recordings

<!-- If applicable, add screenshots or screen recordings to help explain the issue. -->

### Additional Context

<!-- Add any other context about the problem here (e.g. multi-monitor layout, custom title bar widgets, custom window flags, Win32/DWM behavior). -->
