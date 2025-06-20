#include <WiFi.h>
#include "esp_camera.h"
#include "FS.h"
#include "SD.h"
#include "SPI.h"

#define CAMERA_MODEL_XIAO_ESP32S3
#include "camera_pins.h"

// Wi-Fi credentials
const char* ssid = "YOUR_SSID";
const char* password = "YOUR_PASSWORD";

// Web server
WiFiServer server(80);

// Global status
unsigned long lastCaptureTime = 0;
int imageCount = 1;
bool camera_sign = false;
bool sd_sign = false;

// Save pictures to SD card
void photo_save(const char *fileName) {
  camera_fb_t *fb = esp_camera_fb_get();
  if (!fb) {
    Serial.println("Failed to get camera frame buffer");
    return;
  }
  writeFile(SD, fileName, fb->buf, fb->len);
  esp_camera_fb_return(fb);
  Serial.println("Photo saved to file");
}

void writeFile(fs::FS &fs, const char *path, uint8_t *data, size_t len) {
  Serial.printf("Writing file: %s\n", path);
  File file = fs.open(path, FILE_WRITE);
  if (!file) {
    Serial.println("Failed to open file for writing");
    return;
  }
  if (file.write(data, len) == len) {
    Serial.println("File written");
  } else {
    Serial.println("Write failed");
  }
  file.close();
}

// Task to run camera + SD
void TaskCamera(void *pvParameters) {
  while (true) {
    if (camera_sign && sd_sign) {
      unsigned long now = millis();
      if ((now - lastCaptureTime) >= 60000) {
        char filename[32];
        sprintf(filename, "/image%d.jpg", imageCount);
        photo_save(filename);
        Serial.printf("Saved picture：%s\n", filename);
        Serial.println("Photos will begin in one minute, please be ready.");
        imageCount++;
        lastCaptureTime = now;
      }
    }
    vTaskDelay(1000 / portTICK_PERIOD_MS); // Check once per second
  }
}

// Task to run simple web server
void TaskWebServer(void *pvParameters) {
  server.begin();
  while (true) {
    WiFiClient client = server.available();
    if (client) {
      Serial.println("Client connected");
      while (client.connected()) {
        if (client.available()) {
          String request = client.readStringUntil('\r');
          Serial.print("Request: ");
          Serial.println(request);
          client.flush();

          // Send a basic response
          client.println("HTTP/1.1 200 OK");
          client.println("Content-Type: text/html");
          client.println();
          client.println("<h1>Hello from XIAO ESP32S3!</h1>");
          break;
        }
      }
      delay(1);
      client.stop();
      Serial.println("Client disconnected");
    }
    vTaskDelay(10 / portTICK_PERIOD_MS);
  }
}

void setup() {
  Serial.begin(115200);
  while (!Serial);

  // Camera config
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.frame_size = FRAMESIZE_UXGA;
  config.pixel_format = PIXFORMAT_JPEG;
  config.fb_location = CAMERA_FB_IN_PSRAM;
  config.jpeg_quality = 12;
  config.fb_count = 1;

  if (config.pixel_format == PIXFORMAT_JPEG) {
    if (psramFound()) {
      config.jpeg_quality = 10;
      config.fb_count = 2;
      config.grab_mode = CAMERA_GRAB_LATEST;
    } else {
      config.frame_size = FRAMESIZE_SVGA;
      config.fb_location = CAMERA_FB_IN_DRAM;
    }
  } else {
    config.frame_size = FRAMESIZE_240X240;
#if CONFIG_IDF_TARGET_ESP32S3
    config.fb_count = 2;
#endif
  }

  if (esp_camera_init(&config) == ESP_OK) {
    camera_sign = true;
  } else {
    Serial.println("Camera init failed");
  }

  if (SD.begin(21)) {
    uint8_t cardType = SD.cardType();
    if (cardType != CARD_NONE) {
      sd_sign = true;
      Serial.println("SD card initialized");
    } else {
      Serial.println("No SD card attached");
    }
  } else {
    Serial.println("SD card mount failed");
  }

  // Connect to Wi-Fi
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println();
  Serial.print("Connected. IP: ");
  Serial.println(WiFi.localIP());

  Serial.println("Photos will begin in one minute, please be ready.");

  // Create FreeRTOS tasks - multithreading
  xTaskCreatePinnedToCore(TaskCamera, "Camera", 4096, NULL, 1, NULL, 1);
  xTaskCreatePinnedToCore(TaskWebServer, "WebServer", 4096, NULL, 1, NULL, 0);
}

void loop() {
  // Nothing to do here
}
