# Extract Fanfic Metadata 1.4.0

Choose which custom columns the plugin may overwrite.

## New

- **Overwrite, per column.** The column mapping has a new **Overwrite** tick on every row.
  Ticked columns are replaced with the recovered value; unticked columns are only filled
  when empty, so values you or FanFicFare entered are kept. Useful for refreshing Status
  without touching anything else, including anthology columns FanFicFare fills its own way.
  The preview lists the columns that will be kept.

## Changed

- **All Overwrite ticks start off.** Until now custom columns were always replaced. After
  updating, open **Configure column mapping…** and tick the columns you want kept up to
  date, such as Status or the Anthology Story Report. (Coming from 1.2.x or earlier with
  the anthology report set to overwrite? Its tick starts on.)
- "Also for anthologies" is now called **Anthologies too**.
- The column mapping's headings stay in place while you scroll.
