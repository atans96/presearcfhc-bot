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
      "--user-data-dir=C:/Users/allan/AppData/Local/Google/Chrome/User Data/Profile 8",
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

  const checkOffersAvailable = async () => {
    try {
      // wait for elements to load
      await page.waitForSelector("span#clicksTotalOffers");
      await page.waitForSelector("table#viewAdsTOffers1");
      const date = new Date();
      const currentTime = `${date.getHours()}:${date.getMinutes()}:${date.getSeconds()}`;
      // get offer count
      const totalOffers = await page.$eval(
        "span#clicksTotalOffers",
        (el) => el.textContent
      );

      if (Number(totalOffers) <= 0) {
        console.log(
          `Come back later all offers available for today are exhausted ${currentTime}`
        );
        const mins = 4;
        await sleep(mins * 60 * 1000);
        return 1;
      }
      return 3;
    } catch (error) {
      console.error(
        error,
        "Timed out waiting for card-text element to load. Retrying..."
      );
      return 2;
    }
  };

  const foo = async () => {
    let retry = 0;
    while (true) {
      try {
        if (retry === 0) {
          await page.goto(
            "https://timebucks.com/publishers/index.php?pg=earn&tab=view_content_ads",
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
        }
        const url = await page.url();
        if (
          url !==
          "https://timebucks.com/publishers/index.php?pg=earn&tab=view_content_ads"
        ) {
          throw new Error("URL mismatch");
        }
        const status = await checkOffersAvailable();
        if (status === 1 || status === 2) {
          retry = 0;
          continue;
        }
        const pageTarget = page.target();
        await page.waitForSelector("a.btnClickAdd");
        const timer = await page.$eval(
          "a.btnClickAdd",
          (el) => el.dataset.timer
        );
        await page.$eval("a.btnClickAdd", (el) => el.click());
          const newTarget = await browser.waitForTarget(
        
          (target) => target.opener() === pageTarget
        );
        const newPage = await newTarget.page(); //get the page object
        await newPage.waitForSelector("body"); //wait for page to be loaded
        await sleep((Number(timer) + 10) * 1000);
        await newPage.close();
        retry = -1;
      } catch (error) {
        console.error(error);
        retry = 0;
      }
    }
  };

  await foo();
})();
