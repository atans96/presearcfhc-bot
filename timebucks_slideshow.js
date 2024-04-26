import puppeteer from "puppeteer";
import { sleep } from "./utils.js";

(async () => {
  const browser = await puppeteer.launch({
    // headless: "new",
    headless: false,
    args: [
      "--no-sandbox",
      "--disable-setuid-sandbox",
      "--disable-infobars",
      "--disable-dev-shm-usage",
      "--disable-accelerated-2d-canvas",
      "--no-first-run",
      "--no-zygote",
      "--disable-gpu",
      "--window-position=0,0",
      "--ignore-certifcate-errors",
      "--ignore-certifcate-errors-spki-list",
      "--mute-audio",
      "--user-data-dir=C:/Users/allan/AppData/Local/Google/Chrome/User Data/Profile 13",
    ],
  });
  const page = await browser.newPage();
  page.on("dialog", async (dialog) => {
    await dialog.dismiss();
  });

  const closeAllTabs = async () => {
    for (let i = 1; i < browser.pages().length; i++) {
      const tab = browser.pages()[i];
      await tab.close();
    }
  };

  const waitUntilTimersFinish = async (newPage) => {
    while (true) {
      try {
        await newPage.waitForSelector(
          "xpath/" +
            "//*[contains(@id, 'next-pre-blow')]//div[2][contains(@style, 'display: block')]",
          { timeout: 60_000 }
        );
        await sleep(1000);
        await newPage.$eval("div.next_btn > a", (el) => el.click());
        await newPage.waitForNavigation({ waitUntil: "load" });
        await newPage.waitForSelector("body");
        const url = await newPage.evaluate(() => document.location);
        if (url.origin === "https://timebucks.com") {
          return false;
        }
      } catch (e) {
        console.error(e);
        await newPage.reload();
        continue;
        // return false;
      }
    }
  };

  const checkOffersAvailable = async () => {
    try {
      const [offers, time] = await Promise.all([
        page.$eval("#totalOffersRemainingToday", (el) => el.innerText),
        page.$eval("#totalTimeRemaining", (el) => el.innerText),
      ]);
      const date = new Date();
      const currentTime = `${date.getHours()}:${date.getMinutes()}:${date.getSeconds()}`;

      if (offers <= 0) {
        console.log(
          `Come back later all offers available for today are exhausted ${currentTime}`
        );
        const mins = 30;
        await sleep(mins * 60 * 1000);
        return 1;
      } else if (offers > 0 && time.includes("min")) {
        const mins = parseInt(time.replace(" min", ""));
        const waitSeconds = mins * 60;
        console.log(`Come back later in ${mins} minutes ${currentTime}`);
        await sleep(waitSeconds * 1000);
        return 1;
      } else if (offers > 0) {
        return 3;
      }
    } catch (error) {
      console.error(
        error,
        "Timed out waiting for card-text element to load. Retrying..."
      );
      return 2;
    }
  };

  const foo = async () => {
    while (true) {
      try {
        await page.goto(
          "https://timebucks.com/publishers/index.php?pg=earn&tab=view_content_timecave_slideshows",
          {
            timeout: 60_000,
            waitUntil: [
              "domcontentloaded",
              "networkidle0",
              "networkidle2",
              "load",
            ],
          }
        );
        const url = await page.url();
        if (
          url !==
          "https://timebucks.com/publishers/index.php?pg=earn&tab=view_content_timecave_slideshows"
        ) {
          throw new Error("URL mismatch");
        }
        const status = await checkOffersAvailable();
        if (status === 1 || status === 2) {
          continue;
        }
        const pageTarget = page.target();
        await page.$eval("a.btnSlideShow", (el) => el.click());
        const newTarget = await browser.waitForTarget(
          (target) => target.opener() === pageTarget
        );
        const newPage = await newTarget.page(); //get the page object
        await newPage.waitForSelector("body"); //wait for page to be loaded
        await newPage.waitForFunction(
          'window.location.origin.includes("thetimecave.com")'
        );
        await waitUntilTimersFinish(newPage);
        await newPage.close();
      } catch (error) {
        console.error(error);
        continue;
      }
    }
  };

  await foo();
})();
