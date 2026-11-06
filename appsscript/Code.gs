/**
 * 鮨おまかせ図鑑 — 訪客投稿收件端
 * 收到 {fish, venue, comment, submitter, image(dataURL)} → 存 Drive + 寫 Sheet(pending)
 * 只有 jjh 批核（狀態=approved）嘅投稿先會出現在網站。
 */
var SHEET_ID  = '1rmeRMt6k7FN4rD9QKwatnP4HUjNV9hbH_hA-jD4f0qg';
var FOLDER_ID = '1w_OIV2C6bFxGBbtNUHcuXAJpBB_nMqwv';
var MAX_BYTES = 6 * 1024 * 1024;

function doGet() {
  return ContentService
    .createTextOutput(JSON.stringify({ok: true, service: 'omakase-upload', v: 1}))
    .setMimeType(ContentService.MimeType.JSON);
}

function doPost(e) {
  try {
    var raw = (e && e.postData && e.postData.contents) || '{}';
    var p = JSON.parse(raw);
    if (!p.image || !p.fish) throw new Error('missing image or fish');

    var b64 = String(p.image).split(',')[1] || String(p.image);
    var mime = String(p.image).match(/^data:(image\/[a-z+]+);/i);
    mime = mime ? mime[1] : 'image/jpeg';
    var bytes = Utilities.base64Decode(b64);
    if (bytes.length > MAX_BYTES) throw new Error('image too large');

    var stamp = Utilities.formatDate(new Date(), 'Asia/Hong_Kong', 'yyyyMMdd-HHmmss');
    var safe = String(p.fish).replace(/[^\w\u3040-\u30ff\u4e00-\u9fff]/g, '');
    var name = stamp + '_' + safe + '.jpg';

    var blob = Utilities.newBlob(bytes, mime, name);
    var file = DriveApp.getFolderById(FOLDER_ID).createFile(blob);

    var ss = SpreadsheetApp.openById(SHEET_ID);
    var sh = ss.getSheetByName('submissions');
    sh.appendRow([
      new Date(),
      String(p.fish).slice(0, 40),
      String(p.venue || '').slice(0, 80),
      String(p.comment || '').slice(0, 400),
      name,
      file.getId(),
      'pending',
      String(p.submitter || '').slice(0, 40)
    ]);

    return ContentService
      .createTextOutput(JSON.stringify({ok: true, id: file.getId()}))
      .setMimeType(ContentService.MimeType.JSON);
  } catch (err) {
    return ContentService
      .createTextOutput(JSON.stringify({ok: false, error: String(err)}))
      .setMimeType(ContentService.MimeType.JSON);
  }
}
