# hands-dienstplan

Turns the shared Hands-Dienstplan Google Sheet into an `.ics` file you can
import into Google Calendar.

## Usage

1. Create your own `config.py` file. Add to it two constants
   1. Write `LINK = "the link of the google sheet"`, the quotation marks "" need to be there. The link is just the standard browser adress, it starts something like `https://docs.google.com/spreadsheets`.
   2. `NAME = "Lastname"` write it exactly as it appears in the sheet.
2. Run it by running

   ```
   python main.py
   ```
   in the terminal. You need to have python installed.

3. Import the generated `dienstplan.ics` in Google Calendar under
   Settings -> Import & export -> Select file from your computer.

Events look like:

* Title: `Hands: Location`
* Location: `Location`
* Description: `TÄ: Tätigkeit` / `PL: Produktionsleiter`

Re-importing an updated file overwrites the matching events instead of
duplicating them, as long as a shift's time, place and task are unchanged.
