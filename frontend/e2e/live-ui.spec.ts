import {test, expect} from "@playwright/test";

test("camera connection choices, presets, and safe validation", async ({page, request}) => {
  const camera = await (await request.post("/api/cameras", {data: {name: "Connection UI verification"}})).json();
  await page.goto("/cameras");
  const card = page.locator(".camera-card").filter({has: page.getByRole("heading", {name: "Connection UI verification", exact:true})}).last();
  const type = card.getByLabel("Connection type for Connection UI verification");
  await expect(type).toBeVisible();
  await card.getByLabel("Camera preset").selectOption("hikvision");
  await expect(card.getByLabel("Recorder channel")).toBeVisible();
  await card.getByLabel("Camera preset").selectOption("custom");
  await type.selectOption("http");
  await card.getByLabel("Stream URL for Connection UI verification").fill("file:///not-a-network-stream");
  await card.getByRole("button", {name: "Connect & record"}).click();
  await expect(card.getByRole("alert")).toContainText("valid camera stream URL");
  await type.selectOption("rtsp");
  await expect(card.getByLabel("Stream URL for Connection UI verification")).toHaveValue("");
  const status = await (await request.get("/api/cameras")).json();
  expect(status.find((c:any) => c.id === camera.id).live.status).toBe("STOPPED");
});
