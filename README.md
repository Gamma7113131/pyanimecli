# pyanimecli
![PyPI version](https://img.shields.io/pypi/v/pyanimecli.svg)
![Build](https://github.com/Gamma7113131/pyanimecli/actions/workflows/publish.yml/badge.svg)
![License](https://img.shields.io/pypi/l/pyanimecli.svg)
![Downloads](https://img.shields.io/pypi/dm/pyanimecli.svg)


A powerful command-line interface for searching, getting info, and watching anime directly from your terminal, powered by the [YumaAPI](https://yumaapi.vercel.app/).

<img width="500" height="500" alt="pyanimecli" src="https://github.com/user-attachments/assets/1007f6a2-f3c9-4f9c-97d6-2139e2958c75" />

---

## 🚀 Features

- 🔍 **Search:** Find any anime by title.
- 📋 **Detailed Info:** Descriptions, episode lists, genres, and more.
- 🎬 **Stream with VLC:** Watch subbed or dubbed episodes in VLC Media Player.
- 💬 **Automatic Subtitles:** Automatically loads subtitles for subbed streams.
- 🌟 **Discover:** Browse recently updated episodes, top airing anime, and spotlight series.
- 🧭 **Explore:** Search by genre or studio.
- 📆 **Schedule:** View airing schedules by date.
- 💻 **Cross-Platform:** Works on Linux, macOS, and Windows.
- 🎨 **Rich Formatting:** Clean, colorful, and easy-to-read output in your terminal.

---

## 📦 Installation

### From PyPI (Recommended)


```bash
pip install pyanimecli
````

> Make sure your `pip` points to Python 3.11+ (e.g., use `pip3` if needed).

### From Git (Latest)

```bash
pip install git+https://github.com/Gamma7113131/pyanimecli.git
```

> This installs the latest commit from the repository’s main branch.

---

## 🛠 Prerequisites

1. **Python 3.11+**
2. **VLC Media Player:** Must be installed and accessible from your system's PATH. [Download VLC](https://www.videolan.org/vlc/)
3. **Required CLI Utilities:**

   * On **Linux/macOS**: `wget`
   * On **Windows**: `curl` (comes pre-installed on Windows 10+)
4. **FFmpeg**

---

## 🧪 Usage

Get a full list of commands:

```bash
pyanimecli -h
```

---

### 📖 Command Examples

#### 1. Search for an anime:

```bash
pyanimecli -s "Attack on Titan"
```

#### 2. Get detailed info for an anime (using the ID from the search results):

```bash
pyanimecli -i "attack-on-titan-3d"
```

#### 3. Watch an episode:

```bash
# Watch a subbed episode
pyanimecli -w "attack-on-titan-3d$episode$571" sub

# Watch a dubbed episode
pyanimecli -w "attack-on-titan-3d$episode$571" dub
```

#### 4. Browse Recently Updated Episodes:

```bash
pyanimecli -re
```

#### 5. Browse Top Airing Anime:

```bash
pyanimecli -ta
```

#### 6. Use Pagination:

```bash
pyanimecli -ta -p 2
```

#### 7. List and Search Genres:

```bash
# List all genres
pyanimecli -g

# Search for anime in the 'action' genre
pyanimecli -gs "action"
```

#### 8. View the Airing Schedule:

```bash
pyanimecli -sc 2025-07-04
```

---

## ⚠️ Disclaimer

This tool is created for educational purposes only. All content is sourced from the publicly available [YumaAPI](https://yumaapi.vercel.app/). Please respect the rights and policies of the original content providers.
