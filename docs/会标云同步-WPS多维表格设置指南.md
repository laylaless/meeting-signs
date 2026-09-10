# 会标云同步 — WPS 多维表格设置指南

目标：管理人员在 WPS 填会标配置 → 会标电脑输入共享码取用。共享码自定义、5 分钟自动过期。

## 一、新建多维表格

1. 浏览器打开 **kdocs.cn**（或 WPS 客户端首页）→ 登录
2. 新建 → **多维表格**（空白）
3. 重命名为「**会标配置**」

> 注意：必须是「多维表格」，不是普通表格/智能表格（脚本接口不同）。

## 二、建数据表字段

在默认数据表（重命名「配置表」）里按此建列，**字段名务必一字不差**（脚本按字段名读取）：

| 字段名 | 类型 | 必填 | 说明 |
|---|---|---|---|
| 共享码 | 文本 | ✓ | 管理员自定义，如 `0910`、`A3` |
| 会议名称 | 多行文本 | ✓ | 可含换行（多行标题） |
| 日期 | 日期 | | 留空 = 当天 |
| 名称字号 | 数字 | | 留空 = 默认 66 |
| 日期字号 | 数字 | | 留空 = 默认 30 |
| 背景色 | 文本 | | 留空 = 政务红，如 `#a52615` |
| 文字色 | 文本 | | 留空 = 黄 |
| 完整JSON | 多行文本 | | 高级：填了则覆盖以上全部 |
| 修改时间 | **修改时间**（自动字段类型） | | 自动记录，**勿手填**；5 分钟过期以它为准 |

## 三、建表单视图（管理人员填报入口）

1. 数据表上方「+ 新建视图」→ **表单视图**，命名「发布表单」
2. 拖入字段：共享码、会议名称、日期必填；字号/颜色/完整JSON 选填
3. 表单右上「分享」→ 开启「**获得链接的任何人可填写**」→ 复制链接/二维码发给管理人员
   - 填表人只见表单，看不到全表
   - 同一码再次提交 = 新记录，客户端取**最新一条**

> 你自己也可以不走表单：直接在表格视图里改行，改完「修改时间」自动刷新（等于续期 5 分钟）。

## 四、装 AirScript 脚本

1. 顶部「**效率**」（或高级功能）→「**高级开发**」→「**AirScript 脚本编辑器**」
2. 左侧选「**文档共享脚本**」（不要放「我的脚本」——不支持 webhook）
3. 新建脚本（若区分版本选 **2.0**；报错再试 1.0），命名「取码」，粘贴：

```js
// 会标取码：按共享码取最新一条，5 分钟内有效；顺带清理 24 小时前的历史行
function main() {
  cleanup();   // 每次取码先清一次旧记录（失败不影响取码）

  var code = String((Context.argv && Context.argv.code) || '').trim();
  if (!code) return { ok: false, msg: '缺少共享码参数' };

  var sheets = Application.Sheet.GetSheets();
  var sheet = null;
  for (var i = 0; i < sheets.length; i++) {
    if (sheets[i].name === '配置表') { sheet = sheets[i]; break; }
  }
  if (!sheet) sheet = sheets[0];

  var all = [], offset = null;
  do {
    var res = Application.Record.GetRecords({ SheetId: sheet.id, Offset: offset });
    all = all.concat(res.records || []);
    offset = res.offset;
  } while (offset);

  var rows = all.filter(function (r) {
    return String(r.fields['共享码'] || '').trim() === code;
  });
  if (!rows.length) return { ok: false, msg: '共享码不存在' };

  rows.sort(function (a, b) {
    return new Date(b.fields['修改时间']) - new Date(a.fields['修改时间']);
  });
  var f = rows[0].fields;

  var ts = new Date(f['修改时间']).getTime();
  if (isNaN(ts) || Date.now() - ts > 5 * 60 * 1000)
    return { ok: false, msg: '共享码已过期（超过5分钟），请重新发布' };

  if (f['完整JSON']) {
    try { return { ok: true, banner: JSON.parse(f['完整JSON']) }; }
    catch (e) { return { ok: false, msg: '完整JSON 格式错误: ' + e.message }; }
  }

  var b = {
    title: String(f['会议名称'] || ''),
    date: f['日期'] ? new Date(f['日期']).toISOString().slice(0, 10)
                    : new Date().toISOString().slice(0, 10)
  };
  if (f['名称字号']) b.titleSize = Number(f['名称字号']);
  if (f['日期字号']) b.dateSize = Number(f['日期字号']);
  if (f['背景色']) b.bg = String(f['背景色']);
  if (f['文字色']) b.fg = String(f['文字色']);
  return { ok: true, banner: b };
}

// 删除修改时间超过 24 小时的历史行（保留当天发布的，防误删）
function cleanup() {
  try {
    var sheets = Application.Sheet.GetSheets();
    var sheet = null;
    for (var i = 0; i < sheets.length; i++) {
      if (sheets[i].name === '配置表') { sheet = sheets[i]; break; }
    }
    if (!sheet) return;
    var all = [], offset = null;
    do {
      var res = Application.Record.GetRecords({ SheetId: sheet.id, Offset: offset });
      all = all.concat(res.records || []);
      offset = res.offset;
    } while (offset);
    var deadline = Date.now() - 24 * 60 * 60 * 1000;
    var ids = all.filter(function (r) {
      var ts = new Date(r.fields['修改时间']).getTime();
      return !isNaN(ts) && ts < deadline;
    }).map(function (r) { return r.id; });
    if (ids.length) Application.Record.DeleteRecords({ SheetId: sheet.id, RecordIds: ids });
  } catch (e) { /* 清理失败不阻塞取码 */ }
}
```

> 已内置**惰性清理**：每次有人取码，自动删掉 24 小时前的旧行——不配置任何定时任务，表也永远干净。若还想每天兜底扫一遍（长期无人取码时也清），见第七节。

4. **Ctrl+S 保存** → 点工具栏「运行」旁的调试按钮可先在网页里测（默认 argv 为空，会返回「缺少共享码参数」，属正常）

## 五、生成令牌 + webhook（只做一次）

1. 工具栏「**脚本令牌**」→ 生成（可能要求先实名认证）→ **令牌只显示一次，立即复制保存**
2. 脚本名右侧「⋯」菜单 →「**复制脚本 webhook**」→ 保存 URL
3. 把 `webhook URL` 和 `令牌` 发给 L（用于客户端/中继配置），令牌有效期半年，可随时免费续期

## 六、验证

1. 表格里填一行：共享码 `0910`、会议名称 `XX街道经济工作会议`、日期今天
2. 终端执行（替换 FILE_ID / SCRIPT_ID（从 webhook URL 里取）和令牌）：

```bash
curl -s -X POST 'https://www.kdocs.cn/api/v3/ide/file/FILE_ID/script/SCRIPT_ID/sync_task' \
  -H 'AirScript-Token: 令牌' \
  -H 'Content-Type: application/json' \
  -d '{"Context":{"argv":{"code":"0910"}}}'
```

- 预期：`"status":"finished"` 且 `data.result.ok === true`，`banner` 为会标配置
- 5 分钟后再 curl：应返回 `ok:false, msg:'共享码已过期'`
- 把 code 换成不存在的码：应返回 `共享码不存在`

## 七、历史记录定时清理（可选）

取码脚本已内置惰性清理（每次取码自动删 24 小时前的行），一般无需再配。若希望**长期无人取码时也保持干净**（如节假日），加一个每天定时清理：

> 注意：多维表格「自动化流程」不支持删除操作，删除只能靠 AirScript 脚本定时执行。

1. 在 AirScript 编辑器「文档共享脚本」里再建一个脚本「定时清理」，粘贴：

```js
// 每天定时清理：删除修改时间超过 24 小时的记录
function main() {
  var sheets = Application.Sheet.GetSheets();
  var sheet = null;
  for (var i = 0; i < sheets.length; i++) {
    if (sheets[i].name === '配置表') { sheet = sheets[i]; break; }
  }
  if (!sheet) return { ok: false, msg: '找不到配置表' };

  var all = [], offset = null;
  do {
    var res = Application.Record.GetRecords({ SheetId: sheet.id, Offset: offset });
    all = all.concat(res.records || []);
    offset = res.offset;
  } while (offset);

  var deadline = Date.now() - 24 * 60 * 60 * 1000;
  var ids = all.filter(function (r) {
    var ts = new Date(r.fields['修改时间']).getTime();
    return !isNaN(ts) && ts < deadline;
  }).map(function (r) { return r.id; });

  if (ids.length) Application.Record.DeleteRecords({ SheetId: sheet.id, RecordIds: ids });
  return { ok: true, deleted: ids.length };
}
```

2. Ctrl+S 保存，**手动点一次「运行」验证**：应返回 `{ok:true, deleted:0}`（当天发布的不会被删）
3. 设置定时（二选一，按编辑器实际入口）：
   - 脚本编辑器里：脚本列表右键该脚本 →「定时任务」/「自动化」→ 每天凌晨 3:00 执行
   - 或多维表格「自动化」→ 新建流程 → 触发条件「定时触发」（每天 3:00）→ 执行动作「运行脚本」选「定时清理」

## 常见问题

- **字段读不到 / undefined**：多半是字段名不一致（全角空格、错别字），或记录为空
- **修改时间不刷新**：确认该列字段类型是「修改时间」（自动字段），不是手动填的日期列
- **令牌失效**：半年到期，编辑器里点令牌「延期」，令牌值不变
- 同一码历史行堆积：不影响（脚本只取最新）；取码时和每日定时都会自动清理 24 小时前的旧行
- 想手动清空：表格视图选中旧行直接删，或表单「清空答卷数据」
