/*
**    With thanks to Michael
*/

#include "TimeSyncClass.h"

TimeSyncClass::TimeSyncClass() {}

/**
 * Sets up the time synchronization with the specified timezone.
 *
 * @param timeZone The timezone to set.
 *
 * @return void
 *
 * @throws None
 */
void TimeSyncClass::setup(const char *timeZone)
{
  configTime(0, 0, "pool.ntp.org", "time.nist.gov",  "time.google.com");
  setenv("TZ", timeZone, 1);
  tzset();

  Serial.printf("Timezone set to: %s\r\n", timeZone);
}

/**
 * Checks if the system time is synchronized.
 *
 * @return True if the system time is synchronized, false otherwise.
 *
 * @throws None
 */
bool TimeSyncClass::isSynced()
{
  time_t now;
  time(&now);

  return (bool)(localtime(&now)->tm_year > 120);
}

/**
 * Synchronizes the system time with the NTP service.
 *
 * @param maxTry The maximum number of attempts to synchronize the time.
 *
 * @return True if the system time is synchronized with the NTP service,
 *         False otherwise.
 *
 * @throws None
 */
bool TimeSyncClass::sync(uint16_t maxTry)
{
  time_t now;
  time(&now);
  uint8_t tries = 0;

  Serial.print("Get time from NTP service .");
  do
  {
    time(&now);
    delay(20);
    if ((tries%10)==0)
    {
      Serial.print(". ");
    }
    tries++;
  } while ((localtime(&now)->tm_year <= 120) && (tries < maxTry));

  if (localtime(&now)->tm_year > 120)
    Serial.println(" Synchronized with NTP Service!");
  else  Serial.println(" NOT (YET) SYNCED!");

  return localtime(&now)->tm_year > 120;

}

/**
 * Logs the current time.
 *
 * @return void
 *
 * @throws None
 */
void TimeSyncClass::logTime()
{
  time_t now;
  time(&now);
  struct tm timeinfo = {0};

  if (localtime(&now)->tm_year <= 120)
  {
    Serial.println("Failed to obtain time");
    return;
  }
  Serial.printf("%s", asctime(&timeinfo));
}
