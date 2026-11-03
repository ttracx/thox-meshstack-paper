// QA: open paper.html and the demo at 1280 and 390 px, light and dark; check for
// horizontal scroll and console errors; run the demo's known-answer tests and
// click through its flows; render PDF pages to a contact sheet is done in qa_pdf.py.
const path = require("path");
const fs = require("fs");
const { chromium } = require("playwright");

const ROOT = path.resolve(__dirname, "..");
const PAPER = "file://" + path.join(ROOT, "wp", "paper.html");
const DEMO = "file://" + path.join(ROOT, "dist", "MeshStack_Demo_v1.0.1.html");

(async () => {
  const browser = await chromium.launch();
  const report = [];
  for (const [name, url] of [["paper", PAPER], ["demo", DEMO]]) {
    for (const width of [1280, 390]) {
      for (const scheme of ["light", "dark"]) {
        const ctx = await browser.newContext({ viewport: { width, height: 900 }, colorScheme: scheme, deviceScaleFactor: 1 });
        const page = await ctx.newPage();
        const errors = [];
        page.on("console", (m) => { if (m.type() === "error") errors.push(m.text()); });
        page.on("pageerror", (e) => errors.push(String(e)));
        await page.goto(url, { waitUntil: "load" });
        await page.evaluate(() => document.fonts.ready);
        const sw = await page.evaluate(() => document.documentElement.scrollWidth);
        const cw = await page.evaluate(() => document.documentElement.clientWidth);
        let kat = null, flows = null;
        if (name === "demo") {
          kat = await page.evaluate(() => window.__katOk);
          await page.click("#kDiverge");
          const kout = await page.textContent("#kOut");
          await page.click("#aHub");
          const aout = await page.textContent("#aOut");
          await page.fill("#pL", "256");
          await page.click("#pRun");
          const pout = await page.textContent("#pOut");
          await page.click("#lRun");
          const lout = await page.textContent("#lOut");
          flows = { keyChanged: kout.includes("<- changed"), hubPlaced: aout.includes("placed"), placeShort: pout, lora: lout.split("\n")[0] };
        }
        await page.screenshot({ path: path.join(ROOT, "wp", "qa", `${name}-${width}-${scheme}.png`), fullPage: name === "demo" });
        report.push({ name, width, scheme, scrollWidth: sw, clientWidth: cw, hscroll: sw > cw, errors, kat, flows });
        await ctx.close();
      }
    }
  }
  await browser.close();
  fs.writeFileSync(path.join(ROOT, "wp", "qa", "qa_report.json"), JSON.stringify(report, null, 2));
  for (const r of report) console.log(`${r.name} ${r.width} ${r.scheme} hscroll=${r.hscroll} errors=${r.errors.length} kat=${r.kat} ${r.flows ? JSON.stringify(r.flows).slice(0, 160) : ""}`);
})();
