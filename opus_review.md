# 魚種圖鑑｜設計評審（禅/温泉視角）

**核心診斷**：目前是「有日本元素的卡片牆」，但缺了禅美學真正的骨幹——**余白的節奏**與**一點朱的節制**。以下 3 項 impact 最大。

---

## ① 4 欄 grid 殺死「間」——鬆開網格，讓卡片呼吸

4 欄 + 4:3 橫圖，在 1200px 容器下每卡僅約 270px，大字明朝立刻壓迫。溫泉／禅的空間感來自**留白比內容多**，不是靠裝飾。同時魚是橫長生物，4:3 會上下留死空間，改 3:2 更貼形。

```css
.fish-grid{
  display:grid;
  grid-template-columns:repeat(auto-fit,minmax(300px,1fr));
  gap:clamp(2rem,4.5vw,4rem);          /* 原 gap 應放大 2 倍以上 */
  max-width:1120px;                     /* 收窄，寧可 3 欄 */
  margin-inline:auto;
  padding-inline:clamp(1.5rem,6vw,5rem);
}
.fish-card{
  background:#fbf8f1;
  padding:1.25rem 1.25rem 1.6rem;       /* 和紙需要「邊」 */
  border:1px solid rgba(60,45,32,.10);  /* 禅用 hairline，不用陰影 */
  box-shadow:0 1px 0 rgba(255,255,255,.5) inset;
  border-radius:1px;                     /* 近乎直角，拒絕圓潤 */
}
.fish-card figure{
  aspect-ratio:3/2;                      /* 原 4:3 → 3/2 */
  margin:0 0 1.1rem;
  overflow:hidden;
}
.fish-card img{width:100%;height:100%;object-fit:cover;display:block;}
```

---

## ② `grayscale(.86) sepia(.30)` 等於廢掉圖鑑功能

圖鑑的任務是**辨識**，而魚的顏色（金目鯛的朱、鯖的青銀、鮪的赤身）正是辨識關鍵。再者 grayscale 疊 sepia 會塌成單一泥褐，整頁 20 張魚看起來一模一樣。做法：靜態時只做**輕度和紙洗色**（統一氛圍），hover/focus 還原真色——這才是「侘寂的克制」而非「資訊的流失」。

```css
.fish-card img{
  filter:saturate(.72) contrast(1.04) brightness(1.02);
  transition:filter .9s cubic-bezier(.22,.61,.36,1), transform 1.2s cubic-bezier(.22,.61,.36,1);
}
.fish-card:hover img,
.fish-card:focus-within img{
  