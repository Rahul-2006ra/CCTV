import { test, expect } from "@playwright/test";
import path from "node:path";

test("real footage → inference → search → playable clip → alerts → credits", async ({
  page,
  request,
}) => {
  const errors: string[] = [];
  const cameraName = `Local verification camera ${Date.now()}`;
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "CCTV investigation" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Cameras", exact: true }).click();
  await page.getByLabel("Camera name").fill(cameraName);
  await page
    .getByLabel("Restricted zone polygon")
    .fill("[[0,0],[1,0],[1,1],[0,1]]");
  await page.getByRole("button", { name: "Add camera", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: cameraName }).last(),
  ).toBeVisible();
  await page.getByRole("button", { name: "Footage", exact: true }).click();
  await page
    .getByLabel("Upload camera")
    .selectOption({ label: cameraName });
  const uploadResponse = page.waitForResponse(r => r.url().endsWith("/api/videos") && r.request().method() === "POST");
  await page
    .getByTestId("video-upload")
    .setInputFiles(path.resolve("../demo/photographic-test.mp4"));
  const uploaded = await (await uploadResponse).json();
  await expect(
    page
      .locator("tbody tr")
      .filter({ hasText: "photographic-test.mp4" })
      .filter({ hasText: cameraName }),
  ).toContainText("READY", { timeout: 240_000 });
  const video = await (await request.get(`/api/videos/${uploaded.id}`)).json();
  expect(video.status).toBe("READY");
  expect(video.objects).toBeGreaterThan(0);
  expect(video.embeddings).toBeGreaterThan(video.frames);
  const health = await (await request.get("/api/system/health")).json();
  expect(health.vectors).toBeGreaterThan(0);
  await page
    .getByRole("button", { name: "Investigation", exact: true })
    .click();
  const search = page.getByLabel("Search footage");
  await page.getByLabel("Search camera filter").selectOption(video.camera_id);
  await search.fill("Find a person");
  await page
    .getByRole("button", { name: "Search footage", exact: true })
    .click();
  await expect(page.getByRole("heading", {name: "What the footage shows"})).toBeVisible({timeout: 60_000});
  await page.getByRole("button", {name: "Back to results"}).click();
  await expect(page.locator(".result-card").first()).toBeVisible();
  await page.screenshot({
    path: "../docs/investigation-results.png",
    fullPage: true,
  });
  await page.locator(".result-card").first().click();
  const player = page.locator("video");
  await expect(player).toBeVisible({ timeout: 60_000 });
  await expect
    .poll(() => player.evaluate((v: HTMLVideoElement) => v.readyState))
    .toBeGreaterThanOrEqual(2);
  const beforePlayback = await player.evaluate((v: HTMLVideoElement) => v.currentTime);
  await player.evaluate((v: HTMLVideoElement) => {
    v.muted = true;
    return v.play();
  });
  await expect
    .poll(() => player.evaluate((v: HTMLVideoElement) => v.currentTime))
    .toBeGreaterThan(beforePlayback + 0.1);
  await player.evaluate((v: HTMLVideoElement) => v.pause());
  await expect(page.getByLabel("Source timeline")).toBeVisible();
  await expect(page.locator(".details")).toContainText("Track ID");
  await expect(page.getByRole("link", { name: "Download clip" })).toBeVisible();
  await page.getByLabel("Clip start (seconds)").fill("1");
  await page.getByLabel("Clip end (seconds)").fill("2.5");
  await page.getByRole("button", {name: "Generate Clip", exact: true}).click();
  await expect(page.getByRole("link", {name: "Download clip"})).toBeVisible({timeout: 60_000});
  await expect.poll(() => player.evaluate((v: HTMLVideoElement) => v.duration)).toBeCloseTo(1.5, 1);
  const downloadEvent = page.waitForEvent("download");
  await page.getByRole("link", {name: "Download clip"}).click();
  expect(await (await downloadEvent).failure()).toBeNull();
  await page.screenshot({
    path: "../docs/investigation-review.png",
    fullPage: true,
  });
  await page.route("**/api/videos/*/evidence?*", route => route.fulfill({status:503, json:{detail:"Evidence temporarily unavailable"}}));
  await page.getByRole("button", {name: "Generate Clip", exact: true}).click();
  await expect(page.getByRole("alert")).toContainText("Evidence temporarily unavailable");
  await expect(page.getByRole("heading", {name: "What the footage shows"})).toHaveCount(0);
  await page.unroute("**/api/videos/*/evidence?*");
  await page.getByRole("button", { name: "Back to results" }).click();
  await search.fill("Find the person wearing a red shirt");
  const redResponse = page.waitForResponse(r => r.url().endsWith("/api/search") && r.request().method() === "POST");
  await page
    .getByRole("button", { name: "Search footage", exact: true })
    .click();
  if ((await (await redResponse).json()).results.length) {
    await page.getByRole("button", {name: "Back to results"}).click();
  }
  await expect(
    page.getByText("Color filter: red", { exact: false }),
  ).toBeVisible();
  await search.fill("Find a car");
  await page
    .getByRole("button", { name: "Search footage", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "No matching footage found." }),
  ).toBeVisible();
  await page.getByRole("button", { name: /^Alerts/ }).click();
  await expect(page.locator("tbody")).toContainText(
    "Restricted zone intrusion",
  );
  await page
    .getByRole("button", { name: "System / Credits", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Open source credits" }),
  ).toBeVisible();
  await expect(page.locator("tbody")).toContainText(
    "Architecture/reference only",
  );
  await page.screenshot({ path: "../docs/system-credits.png", fullPage: true });
  expect(errors).toEqual([]);
});
