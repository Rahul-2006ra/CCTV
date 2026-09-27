# Live cameras and evidence clips

## Connect a source

1. Open **Cameras**, add a location, then use its **Live connection** panel.
2. Select a connection type:
   - **IP camera / DVR / NVR (RTSP):** choose a Hikvision, Dahua, or Axis preset, or choose **Any brand — custom stream URL**. Presets use the main stream; a recorder channel selects which camera to read. Verify the path for your particular model.
   - **HTTP stream:** enter a direct HTTP(S) HLS or MJPEG stream URL, not the camera's web login page.
   - **USB / built-in camera:** select a camera physically connected to the backend computer. Device enumeration currently supports macOS AVFoundation and Linux V4L2. Permit camera access in the operating system when prompted.
3. Set a recording duration (1–480 minutes, default 60), then **Connect & record**.
4. The preview updates every three seconds. Finalized 30-second recordings automatically enter the existing detection, tracking, embedding, and event pipeline. Open **Footage** for indexing progress; only READY recordings are searchable.
5. **Stop recording** finalizes the last partial recording. Saved footage remains available for searching, playback, download, and deletion.

The backend computer must be able to reach the stream. The camera may need RTSP enabled and a dedicated local account. Special characters in a custom URL's username/password must be URL encoded; preset credential fields do this automatically. Generic support depends on the device exposing a compatible stream. Proprietary cloud-only cameras, vendor login flows, ONVIF discovery, PTZ control, and direct Windows USB capture are not implemented.

Source URLs and passwords stay in memory for the recording session. They are not stored in SQLite, returned in API responses, or written to capture logs. FFmpeg receives the URL as a process argument, so a local user with process-inspection permission may see it. Re-enter the connection after a server restart. Keep this unauthenticated prototype bound to loopback; it is not a remotely accessible multi-user recorder.

## Recording behavior

- At most two simultaneous sources. Capture stops if the processing backlog reaches six videos or free disk space falls below 512 MB. A final partial segment can add another job during shutdown.
- Interrupted streams get three reconnection attempts with bounded input timeouts. The UI shows connection, recording, reconnection, stop, and failure states.
- Capture normalizes video to H.264, at most 1280 pixels wide, 15 FPS, without audio. Preview is refreshed still imagery, not full-motion browser streaming.
- Search latency includes the current 30-second segment plus indexing time. Tracking resets at segment boundaries. Events spanning boundaries appear as separate recording matches.
- `recorded_at` is approximate computer reception time, not a verified camera timestamp. Existing uploaded videos retain source-relative timestamps.
- Recordings have a configured session duration, not automatic deletion/retention. Delete unwanted recordings in Footage. Abrupt process/OS crashes can leave incomplete files under `data/live`; normal stop finalizes valid footage. Sessions do not restart automatically.

## Describe an incident and download the matching clip

Enter a description in **Investigation**. The strongest visual match opens directly in the evidence view; **Back to results** shows other matches.

The evidence report summarizes the selected interval, detected object counts, per-recording track observations, measured colors, image-relative motion, and existing rule signals. Expand **Frame-by-frame observations** to inspect timestamps. This is a deterministic report from stored detections, not a video language model or crime classifier. A crime description guides visual similarity search; a match does not establish that the described action happened. Short actions may be missed at the default 1 FPS sampling rate.

The initial clip covers the matched sample interval plus one sample period. Edit **Clip start (seconds)** and **Clip end (seconds)**, then **Generate Clip**. Optionally include surrounding context (configured padding, default ten seconds on either side). **Download clip** exports the currently generated MP4. Partial cuts are re-encoded and decoded for validation; trim timing is limited to video frame resolution. Review and adjust boundaries to isolate the event you see. Automatic exact crime onset/end detection is not implemented.

## API additions

| Endpoint | Purpose |
| --- | --- |
| `GET /api/camera-devices` | Enumerate local USB/built-in video sources |
| `POST /api/cameras/{id}/connect` | `{url, source_type: "rtsp" | "http" | "usb", duration_minutes: 60}` |
| `POST /api/cameras/{id}/stop` | Stop capture and finalize the last recording |
| `GET /api/cameras` | Camera metadata with live status, message, preview availability, and saved segment count |
| `GET /api/cameras/{id}/preview` | Current JPEG, uncached; 404 until a fresh frame exists |
| `GET /api/videos/{id}/evidence?start=0&end=10` | Grounded interval report |
| `POST /api/clips` | Accepts `context: false` for the exact selected interval; defaults to prior context behavior |

Implementation references: [FFmpeg segmentation and image output](https://ffmpeg.org/ffmpeg-formats.html), [FFmpeg network protocols](https://ffmpeg.org/ffmpeg-protocols.html), [Hikvision RTSP](https://supportusa.hikvision.com/support/solutions/articles/17000129064-how-do-i-get-my-rtsp-stream-), [Axis RTSP endpoints](https://developer.axis.com/video-streaming-and-recording/video-streaming/reference/rtsp-endpoints/), [Dahua stream URL documentation](https://materialfile.dahuasecurity.com/uploads/cpq/DOR/PUM0003103/202505/Dahua_Network_Speed_Dome___PTZ_Camera_Web_3.0_User_Manual_V3.0.4.pdf).
