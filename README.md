# 方格子文章轉換器

將方格子(Vocus)網站文章轉換為PDF和Markdown格式，自動下載圖片並整理。

## 快速開始

### 1. 安裝依賴

#### 方式一：使用Conda（推薦）
```bash
# 創建並激活環境
conda env create -f environment.yml
conda activate vocus-converter
```

#### 方式二：使用pip
```bash
pip install -r requirements.txt
```

### 2. 使用方法

#### 轉換單個文章
```bash
python vocus_converter.py "article_html/你的文章.html"
```

#### 批量轉換多個文章
```bash
# 基本批量轉換（智能檢測重複）
python batch_convert.py "article_html/*.html"

# 自動跳過已轉換的文章
python batch_convert.py "article_html/*.html" --skip-existing

# 強制重新轉換所有文章
python batch_convert.py "article_html/*.html" --force-overwrite

# 非互動模式（預設只轉換新文章）
python batch_convert.py "article_html/*.html" --non-interactive
```

### 3. 檔案結構

- **vocus_converter.py** - 主要轉換程式
- **batch_convert.py** - 批量處理程式  
- **article_html/** - 放置原始HTML檔案
- **output/pdf/** - 輸出PDF檔案
- **output/md/** - 輸出Markdown檔案
- **images/** - 下載的圖片檔案
- **utils/** - 輔助工具

### 4. 功能特色

- ✅ 自動下載並嵌入圖片
- ✅ 清理UI控制元素
- ✅ 移除廣告內容
- ✅ 修正編號問題
- ✅ 生成圖片URL清單
- ✅ 支援PDF和Markdown雙格式輸出
- ✅ 智能檢測已轉換文章（避免重複處理）
- ✅ 互動式批量處理選項
- ✅ 檔案修改時間比較（確保最新版本）
- ✅ 自動提取並記錄文章最後修改時間

## 智能重複檢測

系統會自動檢測文章是否已經轉換過，避免重複處理：

### 檢測邏輯
- 檢查對應的PDF和Markdown檔案是否存在
- 比較輸出檔案與HTML源檔案的修改時間
- 顯示詳細狀態：`已存在且較新`、`已存在但較舊`、`部分已存在`

### 處理模式
1. **互動模式**（預設）：詢問用戶選擇處理方式
2. **跳過模式**（`--skip-existing`）：自動跳過已轉換的文章
3. **強制模式**（`--force-overwrite`）：重新轉換所有文章
4. **非互動模式**（`--non-interactive`）：預設只轉換新文章

### 範例輸出
```
找到 5 個HTML檔案
==================================================
檢查已轉換的文章...

已轉換的文章 (3 個):
  ✓ article1.html - 已存在且較新: 文章標題1
  ✓ article2.html - 已存在但較舊: 文章標題2
  ✓ article3.html - 部分已存在: 文章標題3

未轉換的文章 (2 個):
  ○ article4.html - 未轉換: 文章標題4
  ○ article5.html - 未轉換: 文章標題5
```

## 文章資訊提取

系統會自動提取並記錄以下文章資訊：

- **標題**: 從meta標籤或h1標籤提取
- **作者**: 從JSON-LD結構化數據提取
- **發布日期**: 從pubdate meta標籤提取
- **最後修改時間**: 從lastmod或article:modified_time meta標籤提取

這些資訊會顯示在：
- 轉換過程的控制台輸出
- Markdown檔案的頁頭資訊
- PDF檔案的頁眉部分

## 注意事項

- 將下載的HTML檔案放入 `article_html/` 資料夾
- 圖片會自動按日期時間分資料夾儲存
- PDF和Markdown檔案會輸出到對應的 `output/` 子資料夾
- 重複檢測基於文章標題生成的檔案名稱
- 如果文章沒有修改時間資訊，會使用發布時間作為預設值

## 疑難排解

如遇到問題，可使用 `utils/` 資料夾中的輔助工具進行診斷。