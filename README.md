# hands-dienstplan

Turns the shared Hands-Dienstplan Google Sheet into an `.ics` file you can
import into Google Calendar.

## Usage

1. Copy `config.example.py` to `config.py` and set `LINK` (including the
   `#gid=` of the right tab) and `NAME` (as written in column B).
2. Make sure the sheet is shared as "anyone with the link can view".
3. Run it (no dependencies, standard library only):

   ```
   python main.py
   ```

4. Import the generated `dienstplan.ics` in Google Calendar under
   Settings -> Import & export -> Import.

Events look like:

* Title: `Hands: Beethovenhalle`
* Location: `Beethovenhalle`
* Description: `TÄ: ...` / `PL: ...`

Re-importing an updated file overwrites the matching events instead of
duplicating them, as long as a shift's time, place and task are unchanged.
