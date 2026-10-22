# Dataset structure and quality observations

## Scope and measurement

Measured on 2026-10-21 from the local `data/part-0.parquet`, using Python and PyArrow 19.0.1. The scan covers every source row before pipeline transformations, deduplication, rejection, or `ROW_LIMIT` truncation. No values were imputed, normalized, or inferred for these counts.

- Files inspected: **1** (`part-0.parquet`).
- File size: **17,924,094 bytes**.
- Row count: **400,000**, matching the Parquet metadata.
- Columns: **14**.
- SHA-256 before and after inspection: `096d61773b06291768b87490c790755edce5d97d497bd0187694c2e2d7802c56`. The hashes matched; the dataset was not modified.

Existing pipeline reports describe separate runs and can differ from these raw-source counts. In particular, rows rejected for blank titles are included here.

## Actual schema and missing values

Types below are the Arrow schema read from Parquet, in source column order. Every field is marked nullable in the schema; this does not mean every field actually contains nulls. `NULL` means an Arrow null. A blank string is a non-null string that becomes empty after Arrow `utf8_trim_whitespace`; it is counted separately. The two missing-value counts do not overlap. Dashes mean blank-string checks do not apply to that type.

| Field | Arrow type | NULL rows | Blank-string rows | Meaning |
|---|---|---:|---:|---|
| `id` | `string` | 0 | 0 | Source record identifier; pipeline primary key. |
| `job_id` | `string` | 0 | 0 | Additional source job identifier; not globally unique in this file. |
| `company_id` | `int32` | 0 | - | Source company identifier; no company-name lookup is included. |
| `title` | `string` | 0 | 17 | Source job-title text. |
| `department` | `string` | 333,472 | 0 | Source department/category label; not a standardized industry taxonomy. |
| `employment_type` | `string` | 459 | 4,878 | Source employment label; mixed spellings and languages. |
| `workplace_type` | `string` | 0 | 0 | Source workplace label. |
| `country` | `string` | 8,173 | 0 | Source location label; not standardized country codes. |
| `is_remote` | `bool` | 0 | - | Source remote boolean. |
| `posted_at` | `timestamp[us, tz=+00:00]` | 685 | - | Source posting timestamp. |
| `apply_url` | `string` | 0 | 0 | Original application/posting URL; availability not checked. |
| `fetched_time` | `timestamp[us, tz=+00:00]` | 0 | - | Source fetch timestamp. |
| `status` | `string` | 0 | 0 | Source status at capture; not a live vacancy check. |
| `close_time` | `timestamp[us, tz=+00:00]` | 48,483 | - | Source closing timestamp; not a hiring outcome. |

The 17 blank titles have no Arrow null value. `employment_type` has 459 nulls plus 4,878 empty strings, for 5,337 missing labels under the definition above. Department is missing in 83.368% of rows (333,472 / 400,000).

## Identifier duplication

Duplicates use exact source values, without trimming, case changes, or cross-field matching. An extra duplicate row is each occurrence beyond the first for a non-null value.

| Field | Distinct non-null values | NULL rows | Values occurring more than once | Extra duplicate rows |
|---|---:|---:|---:|---:|
| `id` | 400,000 | 0 | 0 | 0 |
| `job_id` | 399,996 | 0 | 4 | 4 |

Each of the four repeated `job_id` values occurs twice. Unique source IDs do not establish that every row represents a distinct real-world vacancy; repostings or multiple source identifiers have not been reconciled.

## Date ranges and chronology

All three timestamp fields use microsecond precision and UTC (`+00:00`). Minimum and maximum exclude null values. These are observed source timestamps, not verified event dates.

| Field | Non-null rows | Minimum (UTC) | Maximum (UTC) |
|---|---:|---|---|
| `posted_at` | 399,315 | `2009-10-29T00:00:00+00:00` | `2030-04-15T00:00:00+00:00` |
| `fetched_time` | 400,000 | `2026-05-24T05:00:09.397933+00:00` | `2026-09-25T13:26:15.618262+00:00` |
| `close_time` | 351,517 | `2026-05-25T02:46:48.775321+00:00` | `2026-09-25T13:26:15.618262+00:00` |

- Rows with both posting and closing timestamps: **351,061**.
- Closing timestamp earlier than posting timestamp: **49** rows.
- Posting timestamp later than that row's fetch timestamp: **185** rows.
- Disagreements between `is_remote` and whether `workplace_type` equals `remote`: **0** rows.

Posting dates extend beyond the fetch window, including a maximum in 2030. Do not treat the raw minimum/maximum as a validated period of market coverage. A close timestamp measures a source closure observation, not time to hire; active records also have no observed completed duration.

## Category values

The tables preserve exact source values, including case, punctuation, multilingual text, and empty strings. Values are shown as JSON literals: `null` is missing, `""` is empty text, and `true`/`false` are booleans. Distinct counts include non-null values (including empty text); no aliases are merged. Tables are ordered by descending frequency, with deterministic string ordering for ties.

| Field | Distinct non-null raw values | NULL rows |
|---|---:|---:|
| `status` | 2 | 0 |
| `workplace_type` | 2 | 0 |
| `is_remote` | 2 | 0 |
| `country` | 281 | 8,173 |
| `employment_type` | 417 | 459 |
| `department` | 1,033 | 333,472 |

### `status`

| Raw value | Rows |
|---|---:|
| <code>&quot;closed&quot;</code> | 351,517 |
| <code>&quot;active&quot;</code> | 48,483 |

### `workplace_type`

| Raw value | Rows |
|---|---:|
| <code>&quot;onsite&quot;</code> | 378,678 |
| <code>&quot;remote&quot;</code> | 21,322 |

### `is_remote`

| Raw value | Rows |
|---|---:|
| <code>false</code> | 378,678 |
| <code>true</code> | 21,322 |

### Interpreting the longer category lists

`country` includes variants such as `Italy` and `Italia`, `Turkey` and `Türkiye`, and the regional label `Middle East & Africa`; 281 distinct labels must not be interpreted as 281 countries. `employment_type` includes `Full time`, `Full Time`, and `Tiempo completo`, along with labels such as `TRUE` and `Violin`. These source values require a documented normalization policy before comparative analysis. `department` is sparse and mixes labels such as `IT Services`, `Technology`, and `Health Care`; it does not establish an occupation or industry classification.

Complete raw frequency tables follow; each includes nulls and sums to 400,000 rows.

<details>
<summary>All country values and counts</summary>

| Raw value | Rows |
|---|---:|
| <code>&quot;United States&quot;</code> | 241,675 |
| <code>&quot;India&quot;</code> | 30,801 |
| <code>&quot;Canada&quot;</code> | 17,156 |
| <code>&quot;United Kingdom&quot;</code> | 15,218 |
| <code>&quot;Australia&quot;</code> | 10,072 |
| <code>null</code> | 8,173 |
| <code>&quot;Germany&quot;</code> | 6,265 |
| <code>&quot;France&quot;</code> | 4,524 |
| <code>&quot;Mexico&quot;</code> | 3,651 |
| <code>&quot;Brazil&quot;</code> | 2,853 |
| <code>&quot;Philippines&quot;</code> | 2,741 |
| <code>&quot;United Arab Emirates&quot;</code> | 2,504 |
| <code>&quot;Spain&quot;</code> | 2,493 |
| <code>&quot;Italy&quot;</code> | 2,477 |
| <code>&quot;China&quot;</code> | 2,384 |
| <code>&quot;Singapore&quot;</code> | 2,249 |
| <code>&quot;Netherlands&quot;</code> | 2,160 |
| <code>&quot;South Africa&quot;</code> | 2,082 |
| <code>&quot;Ireland&quot;</code> | 2,078 |
| <code>&quot;Poland&quot;</code> | 2,033 |
| <code>&quot;Malaysia&quot;</code> | 1,796 |
| <code>&quot;Nigeria&quot;</code> | 1,660 |
| <code>&quot;Egypt&quot;</code> | 1,572 |
| <code>&quot;Switzerland&quot;</code> | 1,528 |
| <code>&quot;Portugal&quot;</code> | 1,522 |
| <code>&quot;Sweden&quot;</code> | 1,378 |
| <code>&quot;Taiwan&quot;</code> | 1,167 |
| <code>&quot;Vietnam&quot;</code> | 1,084 |
| <code>&quot;Finland&quot;</code> | 1,026 |
| <code>&quot;Thailand&quot;</code> | 1,005 |
| <code>&quot;Saudi Arabia&quot;</code> | 975 |
| <code>&quot;Japan&quot;</code> | 964 |
| <code>&quot;Pakistan&quot;</code> | 934 |
| <code>&quot;Colombia&quot;</code> | 913 |
| <code>&quot;Indonesia&quot;</code> | 858 |
| <code>&quot;Belgium&quot;</code> | 847 |
| <code>&quot;Hong Kong&quot;</code> | 817 |
| <code>&quot;Denmark&quot;</code> | 799 |
| <code>&quot;New Zealand&quot;</code> | 789 |
| <code>&quot;Kenya&quot;</code> | 615 |
| <code>&quot;Argentina&quot;</code> | 553 |
| <code>&quot;Costa Rica&quot;</code> | 551 |
| <code>&quot;Austria&quot;</code> | 493 |
| <code>&quot;Czechia&quot;</code> | 488 |
| <code>&quot;Hungary&quot;</code> | 488 |
| <code>&quot;Romania&quot;</code> | 425 |
| <code>&quot;Korea, Republic of&quot;</code> | 349 |
| <code>&quot;Sri Lanka&quot;</code> | 330 |
| <code>&quot;Bulgaria&quot;</code> | 320 |
| <code>&quot;Qatar&quot;</code> | 320 |
| <code>&quot;Chile&quot;</code> | 317 |
| <code>&quot;Uganda&quot;</code> | 308 |
| <code>&quot;Peru&quot;</code> | 293 |
| <code>&quot;Serbia&quot;</code> | 293 |
| <code>&quot;El Salvador&quot;</code> | 285 |
| <code>&quot;Norway&quot;</code> | 282 |
| <code>&quot;Lebanon&quot;</code> | 273 |
| <code>&quot;Guatemala&quot;</code> | 243 |
| <code>&quot;Israel&quot;</code> | 241 |
| <code>&quot;Türkiye&quot;</code> | 240 |
| <code>&quot;Bolivia&quot;</code> | 200 |
| <code>&quot;Honduras&quot;</code> | 190 |
| <code>&quot;Libya&quot;</code> | 177 |
| <code>&quot;Lithuania&quot;</code> | 177 |
| <code>&quot;Cyprus&quot;</code> | 174 |
| <code>&quot;Ecuador&quot;</code> | 167 |
| <code>&quot;Dominican Republic&quot;</code> | 164 |
| <code>&quot;Panama&quot;</code> | 160 |
| <code>&quot;Bangladesh&quot;</code> | 154 |
| <code>&quot;Congo, Democratic Republic of the&quot;</code> | 152 |
| <code>&quot;Greece&quot;</code> | 148 |
| <code>&quot;Ghana&quot;</code> | 146 |
| <code>&quot;Italia&quot;</code> | 144 |
| <code>&quot;Ukraine&quot;</code> | 136 |
| <code>&quot;Jamaica&quot;</code> | 123 |
| <code>&quot;Morocco&quot;</code> | 123 |
| <code>&quot;Estonia&quot;</code> | 115 |
| <code>&quot;Sultanate of Oman&quot;</code> | 111 |
| <code>&quot;Paraguay&quot;</code> | 110 |
| <code>&quot;Uruguay&quot;</code> | 105 |
| <code>&quot;Afghanistan&quot;</code> | 103 |
| <code>&quot;Luxembourg&quot;</code> | 103 |
| <code>&quot;Ethiopia&quot;</code> | 99 |
| <code>&quot;Bahrain&quot;</code> | 98 |
| <code>&quot;Tanzania&quot;</code> | 91 |
| <code>&quot;Papua New Guinea&quot;</code> | 90 |
| <code>&quot;Jordan&quot;</code> | 89 |
| <code>&quot;Haiti&quot;</code> | 83 |
| <code>&quot;Turkey&quot;</code> | 83 |
| <code>&quot;Myanmar&quot;</code> | 82 |
| <code>&quot;España&quot;</code> | 81 |
| <code>&quot;Mauritius&quot;</code> | 79 |
| <code>&quot;Zambia&quot;</code> | 79 |
| <code>&quot;Slovakia&quot;</code> | 77 |
| <code>&quot;Venezuela&quot;</code> | 76 |
| <code>&quot;Namibia&quot;</code> | 71 |
| <code>&quot;Nicaragua&quot;</code> | 71 |
| <code>&quot;South Sudan&quot;</code> | 70 |
| <code>&quot;Armenia&quot;</code> | 67 |
| <code>&quot;Chad&quot;</code> | 65 |
| <code>&quot;Mozambique&quot;</code> | 65 |
| <code>&quot;Kosovo&quot;</code> | 63 |
| <code>&quot;Nepal&quot;</code> | 63 |
| <code>&quot;Mauritania&quot;</code> | 56 |
| <code>&quot;Timor-Leste&quot;</code> | 56 |
| <code>&quot;Zimbabwe&quot;</code> | 54 |
| <code>&quot;Albania&quot;</code> | 53 |
| <code>&quot;Rwanda&quot;</code> | 52 |
| <code>&quot;Yemen&quot;</code> | 47 |
| <code>&quot;Cambodia&quot;</code> | 46 |
| <code>&quot;Sudan&quot;</code> | 46 |
| <code>&quot;België&quot;</code> | 44 |
| <code>&quot;Maroc&quot;</code> | 43 |
| <code>&quot;Senegal&quot;</code> | 43 |
| <code>&quot;Tunisia&quot;</code> | 43 |
| <code>&quot;Malta&quot;</code> | 42 |
| <code>&quot;Somalia&quot;</code> | 42 |
| <code>&quot;Bosnia and Herzegovina&quot;</code> | 41 |
| <code>&quot;Central African Republic&quot;</code> | 41 |
| <code>&quot;Solomon Islands&quot;</code> | 40 |
| <code>&quot;Latvia&quot;</code> | 39 |
| <code>&quot;Saint Kitts and Nevis&quot;</code> | 39 |
| <code>&quot;Trinidad and Tobago&quot;</code> | 39 |
| <code>&quot;Barbados&quot;</code> | 34 |
| <code>&quot;Liberia&quot;</code> | 34 |
| <code>&quot;Malawi&quot;</code> | 34 |
| <code>&quot;State of Palestine&quot;</code> | 33 |
| <code>&quot;Syria&quot;</code> | 32 |
| <code>&quot;Niger&quot;</code> | 31 |
| <code>&quot;Kuwait&quot;</code> | 30 |
| <code>&quot;Fiji&quot;</code> | 29 |
| <code>&quot;Madagascar&quot;</code> | 29 |
| <code>&quot;Burundi&quot;</code> | 28 |
| <code>&quot;Palestinian Territory&quot;</code> | 28 |
| <code>&quot;Algeria&quot;</code> | 27 |
| <code>&quot;Cameroon&quot;</code> | 27 |
| <code>&quot;Iraq&quot;</code> | 27 |
| <code>&quot;Laos&quot;</code> | 27 |
| <code>&quot;Angola&quot;</code> | 25 |
| <code>&quot;Korea&quot;</code> | 24 |
| <code>&quot;Croatia&quot;</code> | 23 |
| <code>&quot;Kazakhstan&quot;</code> | 23 |
| <code>&quot;Viet Nam&quot;</code> | 23 |
| <code>&quot;Mongolia&quot;</code> | 22 |
| <code>&quot;Sierra Leone&quot;</code> | 22 |
| <code>&quot;Burkina Faso&quot;</code> | 20 |
| <code>&quot;日本&quot;</code> | 20 |
| <code>&quot;Gambia&quot;</code> | 19 |
| <code>&quot;Oman&quot;</code> | 19 |
| <code>&quot;Srbija&quot;</code> | 19 |
| <code>&quot;Uzbekistan&quot;</code> | 19 |
| <code>&quot;Bahamas&quot;</code> | 18 |
| <code>&quot;Benin&quot;</code> | 18 |
| <code>&quot;Middle East &amp; Africa&quot;</code> | 18 |
| <code>&quot;Puerto Rico&quot;</code> | 18 |
| <code>&quot;Côte d\\u2019Ivoire&quot;</code> | 17 |
| <code>&quot;Togo&quot;</code> | 17 |
| <code>&quot;Lesotho&quot;</code> | 16 |
| <code>&quot;Virgin Islands (U.S.)&quot;</code> | 15 |
| <code>&quot;Macedonia&quot;</code> | 14 |
| <code>&quot;Moldova&quot;</code> | 14 |
| <code>&quot;Eswatini&quot;</code> | 13 |
| <code>&quot;Suisse&quot;</code> | 13 |
| <code>&quot;Tajikistan&quot;</code> | 13 |
| <code>&quot;Mali&quot;</code> | 12 |
| <code>&quot;Österreich&quot;</code> | 12 |
| <code>&quot;Botswana&quot;</code> | 11 |
| <code>&quot;Djibouti&quot;</code> | 11 |
| <code>&quot;Kosova&quot;</code> | 11 |
| <code>&quot;OCONUS&quot;</code> | 10 |
| <code>&quot;Czech Republic&quot;</code> | 9 |
| <code>&quot;Guernsey&quot;</code> | 9 |
| <code>&quot;Jersey&quot;</code> | 9 |
| <code>&quot;Congo&quot;</code> | 8 |
| <code>&quot;Cote D&#x27;Ivoire (Ivory Coast)&quot;</code> | 8 |
| <code>&quot;Côte d&#x27;Ivoire&quot;</code> | 8 |
| <code>&quot;Democratic Republic of the Congo&quot;</code> | 8 |
| <code>&quot;Guinea&quot;</code> | 8 |
| <code>&quot;Iran&quot;</code> | 8 |
| <code>&quot;Nederland&quot;</code> | 8 |
| <code>&quot;Polska&quot;</code> | 8 |
| <code>&quot;Belarus&quot;</code> | 7 |
| <code>&quot;Montenegro&quot;</code> | 7 |
| <code>&quot;Belize&quot;</code> | 6 |
| <code>&quot;Brunei Darussalam&quot;</code> | 6 |
| <code>&quot;Cayman Islands&quot;</code> | 6 |
| <code>&quot;Moçambique&quot;</code> | 6 |
| <code>&quot;San Marino&quot;</code> | 6 |
| <code>&quot;Slovenia&quot;</code> | 6 |
| <code>&quot;U. S. Virgin Islands&quot;</code> | 6 |
| <code>&quot;المملكة العربية السعودية&quot;</code> | 6 |
| <code>&quot;Allemagne&quot;</code> | 5 |
| <code>&quot;Bhutan&quot;</code> | 5 |
| <code>&quot;Ninguno&quot;</code> | 5 |
| <code>&quot;Panamá&quot;</code> | 5 |
| <code>&quot;República Dominicana&quot;</code> | 5 |
| <code>&quot;Saint Lucia&quot;</code> | 5 |
| <code>&quot;Cape Verde&quot;</code> | 4 |
| <code>&quot;Cognus&quot;</code> | 4 |
| <code>&quot;Emirats Arabes Unis&quot;</code> | 4 |
| <code>&quot;Espagne&quot;</code> | 4 |
| <code>&quot;Ile Maurice&quot;</code> | 4 |
| <code>&quot;Lebanon or Egypt&quot;</code> | 4 |
| <code>&quot;Magyarország&quot;</code> | 4 |
| <code>&quot;Micronesia, Federated States of&quot;</code> | 4 |
| <code>&quot;México&quot;</code> | 4 |
| <code>&quot;Samoa&quot;</code> | 4 |
| <code>&quot;TR&quot;</code> | 4 |
| <code>&quot;Cuba&quot;</code> | 3 |
| <code>&quot;Denmark &amp; Sweden&quot;</code> | 3 |
| <code>&quot;Kyrgyzstan&quot;</code> | 3 |
| <code>&quot;Liechtenstein&quot;</code> | 3 |
| <code>&quot;Macao&quot;</code> | 3 |
| <code>&quot;North Macedonia&quot;</code> | 3 |
| <code>&quot;Russian Federation&quot;</code> | 3 |
| <code>&quot;Slovak Republic&quot;</code> | 3 |
| <code>&quot;U.S.A&quot;</code> | 3 |
| <code>&quot;Vanuatu&quot;</code> | 3 |
| <code>&quot;-None-&quot;</code> | 2 |
| <code>&quot;Africa&quot;</code> | 2 |
| <code>&quot;Andorra&quot;</code> | 2 |
| <code>&quot;Australie&quot;</code> | 2 |
| <code>&quot;Azerbaijan&quot;</code> | 2 |
| <code>&quot;Bermuda&quot;</code> | 2 |
| <code>&quot;Bénin&quot;</code> | 2 |
| <code>&quot;Comoros&quot;</code> | 2 |
| <code>&quot;EC&quot;</code> | 2 |
| <code>&quot;Estados Unidos&quot;</code> | 2 |
| <code>&quot;Gabon&quot;</code> | 2 |
| <code>&quot;Gradding&quot;</code> | 2 |
| <code>&quot;Guinea-Bissau&quot;</code> | 2 |
| <code>&quot;Isle of Man&quot;</code> | 2 |
| <code>&quot;MENA Region&quot;</code> | 2 |
| <code>&quot;Monaco&quot;</code> | 2 |
| <code>&quot;Royaume Uni&quot;</code> | 2 |
| <code>&quot;Svizzera&quot;</code> | 2 |
| <code>&quot;الفيلبين&quot;</code> | 2 |
| <code>&quot;مصر&quot;</code> | 2 |
| <code>&quot;&lt;font _mstmutation=\&quot;1\&quot; _msttexthash=\&quot;153634\&quot; _msthash=\&quot;2676\&quot;&gt;El Salvador&lt;\\/font&gt;&quot;</code> | 1 |
| <code>&quot;Antigua and Barbuda&quot;</code> | 1 |
| <code>&quot;Belge&quot;</code> | 1 |
| <code>&quot;Belice&quot;</code> | 1 |
| <code>&quot;Bosna i Hercegovina&quot;</code> | 1 |
| <code>&quot;CG&quot;</code> | 1 |
| <code>&quot;CONUS&quot;</code> | 1 |
| <code>&quot;Danemark&quot;</code> | 1 |
| <code>&quot;Dubai&quot;</code> | 1 |
| <code>&quot;East Africa Region&quot;</code> | 1 |
| <code>&quot;Equatorial Guinea&quot;</code> | 1 |
| <code>&quot;Eritrea&quot;</code> | 1 |
| <code>&quot;Faroe Islands&quot;</code> | 1 |
| <code>&quot;Federated States of Micronesia&quot;</code> | 1 |
| <code>&quot;Francia&quot;</code> | 1 |
| <code>&quot;French Guiana&quot;</code> | 1 |
| <code>&quot;Geen&quot;</code> | 1 |
| <code>&quot;Greenland&quot;</code> | 1 |
| <code>&quot;Guyana&quot;</code> | 1 |
| <code>&quot;Hong Kong SAR&quot;</code> | 1 |
| <code>&quot;Iceland&quot;</code> | 1 |
| <code>&quot;LY&quot;</code> | 1 |
| <code>&quot;Maldives&quot;</code> | 1 |
| <code>&quot;Marshall Islands&quot;</code> | 1 |
| <code>&quot;Nauru&quot;</code> | 1 |
| <code>&quot;Nenhum&quot;</code> | 1 |
| <code>&quot;Palau&quot;</code> | 1 |
| <code>&quot;Pays Bas&quot;</code> | 1 |
| <code>&quot;Perú&quot;</code> | 1 |
| <code>&quot;Reino Unido&quot;</code> | 1 |
| <code>&quot;Saint Vincent and the Grenadines&quot;</code> | 1 |
| <code>&quot;Sao Tome and Principe&quot;</code> | 1 |
| <code>&quot;Singapour&quot;</code> | 1 |
| <code>&quot;Suriname&quot;</code> | 1 |
| <code>&quot;Swaziland&quot;</code> | 1 |
| <code>&quot;Tonga&quot;</code> | 1 |
| <code>&quot;Tunesien&quot;</code> | 1 |
| <code>&quot;Turkmenistan&quot;</code> | 1 |
| <code>&quot;الأردن&quot;</code> | 1 |
| <code>&quot;اليمن&quot;</code> | 1 |
| <code>&quot;تايلەند&quot;</code> | 1 |
| <code>&quot;سوريا&quot;</code> | 1 |
| <code>&quot;مالیزیا&quot;</code> | 1 |
| <code>&quot;ماينمار&quot;</code> | 1 |

</details>

<details>
<summary>All employment_type values and counts</summary>

| Raw value | Rows |
|---|---:|
| <code>&quot;Full time&quot;</code> | 314,150 |
| <code>&quot;Part time&quot;</code> | 56,528 |
| <code>&quot;&quot;</code> | 4,878 |
| <code>&quot;Permanent&quot;</code> | 2,258 |
| <code>&quot;Temps plein&quot;</code> | 2,154 |
| <code>&quot;Moonlighter&quot;</code> | 2,056 |
| <code>&quot;Contract&quot;</code> | 1,942 |
| <code>&quot;Variable&quot;</code> | 1,561 |
| <code>&quot;Full Time&quot;</code> | 1,124 |
| <code>&quot;Tiempo completo&quot;</code> | 873 |
| <code>&quot;Internship&quot;</code> | 815 |
| <code>&quot;Permanent - temps plein&quot;</code> | 770 |
| <code>&quot;A tempo pieno&quot;</code> | 652 |
| <code>&quot;Casual&quot;</code> | 617 |
| <code>&quot;Freelance&quot;</code> | 561 |
| <code>&quot;Heltid&quot;</code> | 542 |
| <code>&quot;Any&quot;</code> | 499 |
| <code>null</code> | 459 |
| <code>&quot;Tempo integral&quot;</code> | 380 |
| <code>&quot;Permanent - Temps plein&quot;</code> | 374 |
| <code>&quot;Variable time&quot;</code> | 329 |
| <code>&quot;Vollzeit&quot;</code> | 307 |
| <code>&quot;Per Diem&quot;</code> | 257 |
| <code>&quot;Temporary&quot;</code> | 216 |
| <code>&quot;A tempo parziale&quot;</code> | 212 |
| <code>&quot;Temps partiel&quot;</code> | 207 |
| <code>&quot;Self Employed&quot;</code> | 198 |
| <code>&quot;Training&quot;</code> | 187 |
| <code>&quot;Permanent - temps plein / Permanent - Full time&quot;</code> | 172 |
| <code>&quot;Seasonal&quot;</code> | 153 |
| <code>&quot;Non-Guaranteed Hours&quot;</code> | 150 |
| <code>&quot;Temps plein - Permanent&quot;</code> | 148 |
| <code>&quot;Indépendant&quot;</code> | 138 |
| <code>&quot;Regular&quot;</code> | 131 |
| <code>&quot;Full-time&quot;</code> | 124 |
| <code>&quot;ANIMATEUR&quot;</code> | 110 |
| <code>&quot;Light Friday&quot;</code> | 109 |
| <code>&quot;دوام كامل&quot;</code> | 109 |
| <code>&quot;Contrat&quot;</code> | 108 |
| <code>&quot;PRN&quot;</code> | 99 |
| <code>&quot;Emploi permanent&quot;</code> | 84 |
| <code>&quot;Full &amp; Part-Time&quot;</code> | 81 |
| <code>&quot;Full TIme&quot;</code> | 79 |
| <code>&quot;Volunteer&quot;</code> | 78 |
| <code>&quot;Permanent - temps partiel&quot;</code> | 73 |
| <code>&quot;A tempo inteiro&quot;</code> | 72 |
| <code>&quot;Intern&quot;</code> | 71 |
| <code>&quot;Temporaire&quot;</code> | 68 |
| <code>&quot;Voltijds&quot;</code> | 62 |
| <code>&quot;Full Time Employee (FTE)&quot;</code> | 61 |
| <code>&quot;Tempo inteiro&quot;</code> | 60 |
| <code>&quot;Permanent - Temps partiel&quot;</code> | 59 |
| <code>&quot;FTE&quot;</code> | 56 |
| <code>&quot;Parttime&quot;</code> | 53 |
| <code>&quot;Fixed Term&quot;</code> | 46 |
| <code>&quot;Jornada completa&quot;</code> | 46 |
| <code>&quot;Tempo Determinato&quot;</code> | 46 |
| <code>&quot;Existing Business&quot;</code> | 45 |
| <code>&quot;Local Position&quot;</code> | 45 |
| <code>&quot;Temporaire - temps plein&quot;</code> | 42 |
| <code>&quot;Experienced professionals&quot;</code> | 39 |
| <code>&quot;Independent Contractor&quot;</code> | 39 |
| <code>&quot;Nurse - Paediatrics&quot;</code> | 39 |
| <code>&quot;Permanant (Full Time)&quot;</code> | 39 |
| <code>&quot;Stagionale&quot;</code> | 39 |
| <code>&quot;Fulltime&quot;</code> | 38 |
| <code>&quot;Consultancy&quot;</code> | 36 |
| <code>&quot;Puno radno vreme&quot;</code> | 36 |
| <code>&quot;BÉNÉVOLE&quot;</code> | 35 |
| <code>&quot;Full-Time&quot;</code> | 35 |
| <code>&quot;Full Time Equivalent&quot;</code> | 33 |
| <code>&quot;Teilzeit&quot;</code> | 33 |
| <code>&quot;フルタイム&quot;</code> | 33 |
| <code>&quot;New Business&quot;</code> | 32 |
| <code>&quot;Contrato&quot;</code> | 31 |
| <code>&quot;N\\u2019importe lequel&quot;</code> | 31 |
| <code>&quot;NewStore&quot;</code> | 31 |
| <code>&quot;Emploi temporaire&quot;</code> | 25 |
| <code>&quot;Flexible Schedule&quot;</code> | 25 |
| <code>&quot;Permanent - Occasionnel&quot;</code> | 25 |
| <code>&quot;Contractuel - Temps plein&quot;</code> | 23 |
| <code>&quot;New&quot;</code> | 23 |
| <code>&quot;U.S.&quot;</code> | 23 |
| <code>&quot;À temps plein&quot;</code> | 23 |
| <code>&quot;1099&quot;</code> | 22 |
| <code>&quot;Formation&quot;</code> | 22 |
| <code>&quot;Projects&quot;</code> | 21 |
| <code>&quot;Cdi&quot;</code> | 20 |
| <code>&quot;Permanent - temps plein / Full time&quot;</code> | 20 |
| <code>&quot;CDD/CDI&quot;</code> | 19 |
| <code>&quot;Communication/Marketing&quot;</code> | 19 |
| <code>&quot;Partial Year&quot;</code> | 19 |
| <code>&quot;ACCOMPAGNATEUR&quot;</code> | 18 |
| <code>&quot;Consultant&quot;</code> | 18 |
| <code>&quot;Commission Only&quot;</code> | 17 |
| <code>&quot;Tirocinio&quot;</code> | 17 |
| <code>&quot;US Staffing&quot;</code> | 17 |
| <code>&quot;Full time; Part time&quot;</code> | 15 |
| <code>&quot;Medio tiempo&quot;</code> | 15 |
| <code>&quot;Permanent - Temps plein/Full time&quot;</code> | 15 |
| <code>&quot;Apoteke&quot;</code> | 14 |
| <code>&quot;Full time - Onsite&quot;</code> | 14 |
| <code>&quot;Lavori Stagionali&quot;</code> | 14 |
| <code>&quot;DBAS Roles&quot;</code> | 13 |
| <code>&quot;Deltid&quot;</code> | 13 |
| <code>&quot;Pełny etat&quot;</code> | 13 |
| <code>&quot;Saisonnier&quot;</code> | 13 |
| <code>&quot;Tempo Indeterminato&quot;</code> | 13 |
| <code>&quot;Tiempo Completo&quot;</code> | 13 |
| <code>&quot;Full time Consultant&quot;</code> | 12 |
| <code>&quot;Lévis&quot;</code> | 12 |
| <code>&quot;Temporaire - Temps plein&quot;</code> | 12 |
| <code>&quot;Tiempo Indefinido&quot;</code> | 12 |
| <code>&quot;Full / Part Time&quot;</code> | 11 |
| <code>&quot;On-site - Full Time&quot;</code> | 11 |
| <code>&quot;Replacement&quot;</code> | 11 |
| <code>&quot;Sommerakademie&quot;</code> | 11 |
| <code>&quot;SubK&quot;</code> | 11 |
| <code>&quot;Tiempo completo / Temps complet&quot;</code> | 11 |
| <code>&quot;Beliebig&quot;</code> | 10 |
| <code>&quot;Centrala&quot;</code> | 10 |
| <code>&quot;Other&quot;</code> | 10 |
| <code>&quot;contract&quot;</code> | 10 |
| <code>&quot;Apprendistato&quot;</code> | 9 |
| <code>&quot;Contractor&quot;</code> | 9 |
| <code>&quot;Estagiário&quot;</code> | 9 |
| <code>&quot;Full Time, Vacancy Available&quot;</code> | 9 |
| <code>&quot;Full-Time (Hybrid)&quot;</code> | 9 |
| <code>&quot;General Operations&quot;</code> | 9 |
| <code>&quot;Onsite&quot;</code> | 9 |
| <code>&quot;Stagiaire&quot;</code> | 9 |
| <code>&quot;Vollzeit / Teilzeit&quot;</code> | 9 |
| <code>&quot;CRT-FGL (Rivière-du-Loup)&quot;</code> | 8 |
| <code>&quot;Flexible time&quot;</code> | 8 |
| <code>&quot;Full time Seasonal&quot;</code> | 8 |
| <code>&quot;Guaranteed Hours&quot;</code> | 8 |
| <code>&quot;Nord-du-Québec&quot;</code> | 8 |
| <code>&quot;Permanente&quot;</code> | 8 |
| <code>&quot;Stage&quot;</code> | 8 |
| <code>&quot;Student&quot;</code> | 8 |
| <code>&quot;Temporaire - temps plein / Temporary - Full time&quot;</code> | 8 |
| <code>&quot;50%  - 100%&quot;</code> | 7 |
| <code>&quot;Data Analytics&quot;</code> | 7 |
| <code>&quot;Estágio&quot;</code> | 7 |
| <code>&quot;Full/Part Time&quot;</code> | 7 |
| <code>&quot;Healthcare Assistant&quot;</code> | 7 |
| <code>&quot;Lévis ou Boucherville&quot;</code> | 7 |
| <code>&quot;On Contract&quot;</code> | 7 |
| <code>&quot;COORDONNATEUR&quot;</code> | 6 |
| <code>&quot;Efetivo&quot;</code> | 6 |
| <code>&quot;Internship/Co-op&quot;</code> | 6 |
| <code>&quot;Marketing&quot;</code> | 6 |
| <code>&quot;Onsite-Offshore&quot;</code> | 6 |
| <code>&quot;Permanent - Full time&quot;</code> | 6 |
| <code>&quot;Permanent - temps plein ou temps partiel&quot;</code> | 6 |
| <code>&quot;Self-Employed Contract&quot;</code> | 6 |
| <code>&quot;Spontaneous jobs&quot;</code> | 6 |
| <code>&quot;Stage étudiant&quot;</code> | 6 |
| <code>&quot;Temps plein/ Temps partiel&quot;</code> | 6 |
| <code>&quot;Voll-/Teilzeit&quot;</code> | 6 |
| <code>&quot;Banco de talentos&quot;</code> | 5 |
| <code>&quot;Contractuel - Temps partiel&quot;</code> | 5 |
| <code>&quot;Fixed term&quot;</code> | 5 |
| <code>&quot;Intern To Contract To Permanent&quot;</code> | 5 |
| <code>&quot;Jornada Completa&quot;</code> | 5 |
| <code>&quot;Lavori Annuali&quot;</code> | 5 |
| <code>&quot;Libero professionista&quot;</code> | 5 |
| <code>&quot;Ninguno&quot;</code> | 5 |
| <code>&quot;Otvorene prijave&quot;</code> | 5 |
| <code>&quot;Part Time or Full Time&quot;</code> | 5 |
| <code>&quot;Permanent - temps complet&quot;</code> | 5 |
| <code>&quot;Por Proyecto&quot;</code> | 5 |
| <code>&quot;Prácticas Profesionales&quot;</code> | 5 |
| <code>&quot;Remotely&quot;</code> | 5 |
| <code>&quot;Saisonnier/Seasonal&quot;</code> | 5 |
| <code>&quot;Technical&quot;</code> | 5 |
| <code>&quot;Temporaire - temps partiel&quot;</code> | 5 |
| <code>&quot;Temporaire / Temporary&quot;</code> | 5 |
| <code>&quot;Temporary Position&quot;</code> | 5 |
| <code>&quot;Temps Plein&quot;</code> | 5 |
| <code>&quot;4 day work-week&quot;</code> | 4 |
| <code>&quot;A tempo pieno o parziale&quot;</code> | 4 |
| <code>&quot;Alert Roster&quot;</code> | 4 |
| <code>&quot;Ausbildung&quot;</code> | 4 |
| <code>&quot;CLT (Efetivo)&quot;</code> | 4 |
| <code>&quot;Client Relations&quot;</code> | 4 |
| <code>&quot;Communication/Writing&quot;</code> | 4 |
| <code>&quot;Earn While You Learn (EWYL)&quot;</code> | 4 |
| <code>&quot;Employee&quot;</code> | 4 |
| <code>&quot;Fixed Term Contract&quot;</code> | 4 |
| <code>&quot;Freiberufler&quot;</code> | 4 |
| <code>&quot;Full time//Remote Job&quot;</code> | 4 |
| <code>&quot;Full-time Internship&quot;</code> | 4 |
| <code>&quot;Fulltime tijdelijk contract&quot;</code> | 4 |
| <code>&quot;GET-MT Hiring Program&quot;</code> | 4 |
| <code>&quot;Medio Tiempo&quot;</code> | 4 |
| <code>&quot;Montréal&quot;</code> | 4 |
| <code>&quot;Qualquer&quot;</code> | 4 |
| <code>&quot;Teljes állás&quot;</code> | 4 |
| <code>&quot;Temporal&quot;</code> | 4 |
| <code>&quot;Bolsa de empleo&quot;</code> | 3 |
| <code>&quot;Computer Science&quot;</code> | 3 |
| <code>&quot;Contract, Vacancy Available&quot;</code> | 3 |
| <code>&quot;Contractuel / Contractual&quot;</code> | 3 |
| <code>&quot;Contrato permanente&quot;</code> | 3 |
| <code>&quot;Extras&quot;</code> | 3 |
| <code>&quot;FT - Hourly&quot;</code> | 3 |
| <code>&quot;Finance&quot;</code> | 3 |
| <code>&quot;Flexible&quot;</code> | 3 |
| <code>&quot;Full Time / Per Diem&quot;</code> | 3 |
| <code>&quot;Full Time Employee&quot;</code> | 3 |
| <code>&quot;Graduate Scheme&quot;</code> | 3 |
| <code>&quot;Internship (Long term)&quot;</code> | 3 |
| <code>&quot;Internship Program&quot;</code> | 3 |
| <code>&quot;Internships&quot;</code> | 3 |
| <code>&quot;Non Academics&quot;</code> | 3 |
| <code>&quot;Office&quot;</code> | 3 |
| <code>&quot;Piano&quot;</code> | 3 |
| <code>&quot;Sales/Entrepreneurship&quot;</code> | 3 |
| <code>&quot;Stage / Internship&quot;</code> | 3 |
| <code>&quot;Sub Contractor&quot;</code> | 3 |
| <code>&quot;Talent Pool&quot;</code> | 3 |
| <code>&quot;Tam zamanlı&quot;</code> | 3 |
| <code>&quot;Tempo parcial&quot;</code> | 3 |
| <code>&quot;Volunteer/OJT&quot;</code> | 3 |
| <code>&quot;العقد&quot;</code> | 3 |
| <code>&quot;船井総研｜コンサルタント(教育・学校法人・学習塾)&quot;</code> | 3 |
| <code>&quot;80 ou 100%&quot;</code> | 2 |
| <code>&quot;A tempo parcial&quot;</code> | 2 |
| <code>&quot;AmeriCorps (School Year)&quot;</code> | 2 |
| <code>&quot;Arrabet Holding&quot;</code> | 2 |
| <code>&quot;Bank&quot;</code> | 2 |
| <code>&quot;Banque de Candidats&quot;</code> | 2 |
| <code>&quot;College Internship / OJT&quot;</code> | 2 |
| <code>&quot;Consultants&quot;</code> | 2 |
| <code>&quot;Contratto&quot;</code> | 2 |
| <code>&quot;Dowolne&quot;</code> | 2 |
| <code>&quot;Emploi Occasionnel&quot;</code> | 2 |
| <code>&quot;Engineer/Technician&quot;</code> | 2 |
| <code>&quot;Extra Help&quot;</code> | 2 |
| <code>&quot;Fresher&quot;</code> | 2 |
| <code>&quot;Full Time Paid Internship&quot;</code> | 2 |
| <code>&quot;Full Time, Part Time, Bank&quot;</code> | 2 |
| <code>&quot;Full time - Hybrid&quot;</code> | 2 |
| <code>&quot;Full- Time&quot;</code> | 2 |
| <code>&quot;Full- or part time&quot;</code> | 2 |
| <code>&quot;Full/Part time&quot;</code> | 2 |
| <code>&quot;Galenska laboratorija&quot;</code> | 2 |
| <code>&quot;Global Position&quot;</code> | 2 |
| <code>&quot;Hybrid&quot;</code> | 2 |
| <code>&quot;Isle-Maligne&quot;</code> | 2 |
| <code>&quot;Jornada Parcial&quot;</code> | 2 |
| <code>&quot;Minijob&quot;</code> | 2 |
| <code>&quot;New Position&quot;</code> | 2 |
| <code>&quot;Nurse - Adults&quot;</code> | 2 |
| <code>&quot;Offshore&quot;</code> | 2 |
| <code>&quot;On-Demand&quot;</code> | 2 |
| <code>&quot;PERMANENT&quot;</code> | 2 |
| <code>&quot;Part Time - Permanent&quot;</code> | 2 |
| <code>&quot;Part time / Full time&quot;</code> | 2 |
| <code>&quot;Part-Time (Remote)&quot;</code> | 2 |
| <code>&quot;Post Doctoral Fellow&quot;</code> | 2 |
| <code>&quot;Praktikum&quot;</code> | 2 |
| <code>&quot;Project Based&quot;</code> | 2 |
| <code>&quot;Remplacement temporaire&quot;</code> | 2 |
| <code>&quot;Routine Recruitment&quot;</code> | 2 |
| <code>&quot;Sales&quot;</code> | 2 |
| <code>&quot;Sales Support&quot;</code> | 2 |
| <code>&quot;Science/Engineering&quot;</code> | 2 |
| <code>&quot;Service Civique&quot;</code> | 2 |
| <code>&quot;Student Internship&quot;</code> | 2 |
| <code>&quot;Subcontract&quot;</code> | 2 |
| <code>&quot;Temporaire - temps complet&quot;</code> | 2 |
| <code>&quot;Temporaire à permanent&quot;</code> | 2 |
| <code>&quot;Temporary to Permanent&quot;</code> | 2 |
| <code>&quot;Temporär&quot;</code> | 2 |
| <code>&quot;Trainee&quot;</code> | 2 |
| <code>&quot;Volunteer/Student&quot;</code> | 2 |
| <code>&quot;Étudiant&quot;</code> | 2 |
| <code>&quot;コンサルタント&quot;</code> | 2 |
| <code>&quot;船井総研&#124;コンサルタント（空調・電気設備）&quot;</code> | 2 |
| <code>&quot;船井総研｜コンサルタント(医療)&quot;</code> | 2 |
| <code>&quot;船井総研｜コンサルタント(税理士・会計士事務所)&quot;</code> | 2 |
| <code>&quot;13743000000003404&quot;</code> | 1 |
| <code>&quot;41284000000009341&quot;</code> | 1 |
| <code>&quot;Atypical&quot;</code> | 1 |
| <code>&quot;Autónomo/Trabajador independiente&quot;</code> | 1 |
| <code>&quot;Board Appointment&quot;</code> | 1 |
| <code>&quot;Bénévole&quot;</code> | 1 |
| <code>&quot;CAMP MODULO SHERBROOKE&quot;</code> | 1 |
| <code>&quot;COORDONNATEUR ACCOMPAGNEMENT&quot;</code> | 1 |
| <code>&quot;CRT-FGL (Des Neiges)&quot;</code> | 1 |
| <code>&quot;Cdd&quot;</code> | 1 |
| <code>&quot;Closed (Under Review)&quot;</code> | 1 |
| <code>&quot;Contract to Hire&quot;</code> | 1 |
| <code>&quot;Contractuel&quot;</code> | 1 |
| <code>&quot;Contrato Indefinido&quot;</code> | 1 |
| <code>&quot;Costa Rica Staffing&quot;</code> | 1 |
| <code>&quot;Data Engineer&quot;</code> | 1 |
| <code>&quot;Deeltijds&quot;</code> | 1 |
| <code>&quot;Een willekeurige&quot;</code> | 1 |
| <code>&quot;Estágio Profissional&quot;</code> | 1 |
| <code>&quot;Fixed Term (Consultancy)&quot;</code> | 1 |
| <code>&quot;Flexijob&quot;</code> | 1 |
| <code>&quot;Formação&quot;</code> | 1 |
| <code>&quot;Foster Processing&quot;</code> | 1 |
| <code>&quot;Freelance/Contract-to-Hire&quot;</code> | 1 |
| <code>&quot;Fuldtid&quot;</code> | 1 |
| <code>&quot;Full Stack Engineer&quot;</code> | 1 |
| <code>&quot;Full Time Or Part Time&quot;</code> | 1 |
| <code>&quot;Full Time/Part Time&quot;</code> | 1 |
| <code>&quot;Full or Part-time&quot;</code> | 1 |
| <code>&quot;Full time - Permanent&quot;</code> | 1 |
| <code>&quot;Full time fixed term&quot;</code> | 1 |
| <code>&quot;Full time or part time&quot;</code> | 1 |
| <code>&quot;Full time; Part time; Contract&quot;</code> | 1 |
| <code>&quot;Full- time&quot;</code> | 1 |
| <code>&quot;Geen&quot;</code> | 1 |
| <code>&quot;Home Staff&quot;</code> | 1 |
| <code>&quot;IJP or IJR&quot;</code> | 1 |
| <code>&quot;Independent Contract&quot;</code> | 1 |
| <code>&quot;Integral&quot;</code> | 1 |
| <code>&quot;Interinale&quot;</code> | 1 |
| <code>&quot;Intern To Permanent&quot;</code> | 1 |
| <code>&quot;Interns&quot;</code> | 1 |
| <code>&quot;Internship, Vacancy Available&quot;</code> | 1 |
| <code>&quot;Intership&quot;</code> | 1 |
| <code>&quot;Liste de rappel&quot;</code> | 1 |
| <code>&quot;Open for All&quot;</code> | 1 |
| <code>&quot;PT - Hourly&quot;</code> | 1 |
| <code>&quot;Parcial time&quot;</code> | 1 |
| <code>&quot;Part Time&quot;</code> | 1 |
| <code>&quot;Part Time, Vacancy Available&quot;</code> | 1 |
| <code>&quot;Parttime tijdelijk contract&quot;</code> | 1 |
| <code>&quot;Perm or daily rate&quot;</code> | 1 |
| <code>&quot;Permanent - Part time&quot;</code> | 1 |
| <code>&quot;Permanent - Temps plein / Full time&quot;</code> | 1 |
| <code>&quot;Plazo fijo/Indefinido&quot;</code> | 1 |
| <code>&quot;Plein temps&quot;</code> | 1 |
| <code>&quot;Por Tiempo Indefinido&quot;</code> | 1 |
| <code>&quot;Project based&quot;</code> | 1 |
| <code>&quot;Puno radno vreme, Skraćeno radno vreme&quot;</code> | 1 |
| <code>&quot;Qualsiasi&quot;</code> | 1 |
| <code>&quot;Saisonal&quot;</code> | 1 |
| <code>&quot;Selbstständig&quot;</code> | 1 |
| <code>&quot;Students and recent graduates&quot;</code> | 1 |
| <code>&quot;Subcontractor&quot;</code> | 1 |
| <code>&quot;Summer Job&quot;</code> | 1 |
| <code>&quot;Szerződés&quot;</code> | 1 |
| <code>&quot;TRUE&quot;</code> | 1 |
| <code>&quot;Teil- oder Vollzeit&quot;</code> | 1 |
| <code>&quot;Teletrabajo&quot;</code> | 1 |
| <code>&quot;Temporário&quot;</code> | 1 |
| <code>&quot;Tous / All&quot;</code> | 1 |
| <code>&quot;Tous les types&quot;</code> | 1 |
| <code>&quot;Tous les types / All type&quot;</code> | 1 |
| <code>&quot;Traineeship&quot;</code> | 1 |
| <code>&quot;Violin&quot;</code> | 1 |
| <code>&quot;Virtual Internship&quot;</code> | 1 |
| <code>&quot;Vollzeit/Teilzeit&quot;</code> | 1 |
| <code>&quot;W2 Contract&quot;</code> | 1 |
| <code>&quot;Yarı zamanlı&quot;</code> | 1 |
| <code>&quot;x Any Experience&quot;</code> | 1 |
| <code>&quot;دوام جزئي&quot;</code> | 1 |
| <code>&quot;【不動産業界向け】経営コンサルタント&quot;</code> | 1 |
| <code>&quot;【住宅業界】経営コンサルタント&quot;</code> | 1 |
| <code>&quot;【土木・建設業界向け】公共工事コンサルタント&quot;</code> | 1 |
| <code>&quot;【社労士事務所向け】経営コンサルタント あなたの経験・キャリアを経営コンサルティング業務に活かしませんか？&quot;</code> | 1 |
| <code>&quot;いずれでも&quot;</code> | 1 |
| <code>&quot;アプリ系システムエンジニア職(PM/SE/システム企画等)&quot;</code> | 1 |
| <code>&quot;コンサルティングセールス（100億企業化ロードマップ推進部）&quot;</code> | 1 |
| <code>&quot;コンサルティングセールス（IT）&quot;</code> | 1 |
| <code>&quot;コンサルティングセールス（金融機関とのパートナーアライアンス提携）&quot;</code> | 1 |
| <code>&quot;中小中堅企業の「共同経営者」として年商100億を目指す。地方創生を推進する100億企業化経営コンサルタント&quot;</code> | 1 |
| <code>&quot;船井総研&#124;コンサルタント(治療院)&quot;</code> | 1 |
| <code>&quot;船井総研【司法書士/相続事務所向け】経営戦略コンサルタント&quot;</code> | 1 |
| <code>&quot;船井総研｜DX・WEBマーケティングコンサルタント&quot;</code> | 1 |
| <code>&quot;船井総研｜Webメディアのコンテンツ企画及び編集長候補&quot;</code> | 1 |
| <code>&quot;船井総研｜Webメディアの記者・ライター&quot;</code> | 1 |
| <code>&quot;船井総研｜　財務コンサルタント（補助金・ファイナンスコンサルティング部）&quot;</code> | 1 |
| <code>&quot;船井総研｜【建設/土木業界向け】人財・採用戦略コンサルタント&quot;</code> | 1 |
| <code>&quot;船井総研｜【新規事業／編集者・編集長】企業経営者向けのWebメディアの編集者を募集！【プライム上場企業】&quot;</code> | 1 |
| <code>&quot;船井総研｜【製造業界向け】人財・採用戦略コンサルタント&quot;</code> | 1 |
| <code>&quot;船井総研｜アカウントプランナー（広告代理店事業）&quot;</code> | 1 |
| <code>&quot;船井総研｜グローバル軸での多角化を支援するインバウンド・アウトバウンド販路拡大コンサルタント&quot;</code> | 1 |
| <code>&quot;船井総研｜コンサルタント(ESG・脱炭素・カーボンニュートラル)&quot;</code> | 1 |
| <code>&quot;船井総研｜コンサルタント(IPO)&quot;</code> | 1 |
| <code>&quot;船井総研｜コンサルタント(OA機器・IT商社)&quot;</code> | 1 |
| <code>&quot;船井総研｜コンサルタント(アウトドア施設/スキー場・ゴルフ場/レジャー施設/テーマパーク・遊園地/運営/開発/新規事業立ち上げ)&quot;</code> | 1 |
| <code>&quot;船井総研｜コンサルタント(フィットネスジム/インドアゴルフ/プロスポーツ/新規事業立ち上げ)&quot;</code> | 1 |
| <code>&quot;船井総研｜コンサルタント(ポジションマッチ)&quot;</code> | 1 |
| <code>&quot;船井総研｜コンサルタント(モビリティ)&quot;</code> | 1 |
| <code>&quot;船井総研｜コンサルタント(リフォーム業界)&quot;</code> | 1 |
| <code>&quot;船井総研｜コンサルタント(介護)&quot;</code> | 1 |
| <code>&quot;船井総研｜コンサルタント(保険代理店)&quot;</code> | 1 |
| <code>&quot;船井総研｜コンサルタント(再生可能エネルギー)&quot;</code> | 1 |
| <code>&quot;船井総研｜コンサルタント(地方創生)&quot;</code> | 1 |
| <code>&quot;船井総研｜コンサルタント(宿泊施設の新規事業立ちあげ,宿泊施設の業績アップ)&quot;</code> | 1 |
| <code>&quot;船井総研｜コンサルタント(弁護士事務所)&quot;</code> | 1 |
| <code>&quot;船井総研｜コンサルタント(新規事業開発)&quot;</code> | 1 |
| <code>&quot;船井総研｜コンサルタント(歯科医院)&quot;</code> | 1 |
| <code>&quot;船井総研｜コンサルタント(製造業)&quot;</code> | 1 |
| <code>&quot;船井総研｜コンサルタント(金融機関アライアンス室）&quot;</code> | 1 |
| <code>&quot;船井総研｜コンサルタント(障がい福祉)&quot;</code> | 1 |
| <code>&quot;船井総研｜トレーラーハウス＿コンテナハウス立ち上げコンサルタント&quot;</code> | 1 |
| <code>&quot;船井総研｜マーケティング担当&quot;</code> | 1 |
| <code>&quot;船井総研｜モビリティ業界（自動車）エンジニア・DXコンサルタント&quot;</code> | 1 |
| <code>&quot;船井総研｜中央省庁の経験を活かす！地方創生コンサルタント&quot;</code> | 1 |
| <code>&quot;船井総研｜人材開発（採用・評価）コンサルタント&quot;</code> | 1 |
| <code>&quot;船井総研｜住宅リフォーム施工管理コンサルタント&quot;</code> | 1 |
| <code>&quot;船井総研｜土地家屋調査士 経営コンサルタント&quot;</code> | 1 |
| <code>&quot;船井総研｜建材業界コンサルティング&quot;</code> | 1 |
| <code>&quot;船井総研｜持続的な地域コングロマリット経営を目指す/外食産業向けコンサルタント&quot;</code> | 1 |
| <code>&quot;船井総研｜持続的な地域コングロマリット経営を目指す戦略人事コンサルタント&quot;</code> | 1 |
| <code>&quot;船井総研｜生成AI活用研修コンサルタント（住宅・リフォーム業界向け）&quot;</code> | 1 |
| <code>&quot;船井総研｜生産性改善経営コンサルタント【美容室業界向け】&quot;</code> | 1 |
| <code>&quot;船井総研｜財務戦略策定コンサルタント（アカウントパートナー室/中堅企業向け総合経営コンサルティング）&quot;</code> | 1 |
| <code>&quot;金融&quot;</code> | 1 |

</details>

<details>
<summary>All department values and counts</summary>

| Raw value | Rows |
|---|---:|
| <code>null</code> | 333,472 |
| <code>&quot;IT Services&quot;</code> | 6,828 |
| <code>&quot;Technology&quot;</code> | 4,636 |
| <code>&quot;Health Care&quot;</code> | 4,293 |
| <code>&quot;Financial Services&quot;</code> | 2,822 |
| <code>&quot;Education&quot;</code> | 2,355 |
| <code>&quot;Construction&quot;</code> | 1,921 |
| <code>&quot;Retail&quot;</code> | 1,522 |
| <code>&quot;Automotive&quot;</code> | 1,401 |
| <code>&quot;Manufacturing&quot;</code> | 1,334 |
| <code>&quot;Engineering&quot;</code> | 1,285 |
| <code>&quot;Sales - Marketing&quot;</code> | 1,254 |
| <code>&quot;Consulting&quot;</code> | 1,173 |
| <code>&quot;Marketing&quot;</code> | 1,058 |
| <code>&quot;Real Estate&quot;</code> | 1,056 |
| <code>&quot;Hospitality&quot;</code> | 880 |
| <code>&quot;NGO/Social Services&quot;</code> | 815 |
| <code>&quot;Customer Service&quot;</code> | 791 |
| <code>&quot;Telecommunications&quot;</code> | 722 |
| <code>&quot;Solar Energy&quot;</code> | 672 |
| <code>&quot;Energy and Utilities&quot;</code> | 645 |
| <code>&quot;Technologie&quot;</code> | 604 |
| <code>&quot;Advertising&quot;</code> | 547 |
| <code>&quot;Insurance&quot;</code> | 506 |
| <code>&quot;Banking&quot;</code> | 499 |
| <code>&quot;Nonprofit Charitable Organizations&quot;</code> | 499 |
| <code>&quot;FMCG/Foods/Beverage&quot;</code> | 488 |
| <code>&quot;Medical&quot;</code> | 469 |
| <code>&quot;Sanidad&quot;</code> | 469 |
| <code>&quot;Administration&quot;</code> | 464 |
| <code>&quot;Media&quot;</code> | 453 |
| <code>&quot;Logistics&quot;</code> | 443 |
| <code>&quot;Accounting&quot;</code> | 432 |
| <code>&quot;Social Services&quot;</code> | 399 |
| <code>&quot;Architecture &amp; Construction&quot;</code> | 371 |
| <code>&quot;Government/Military&quot;</code> | 368 |
| <code>&quot;Environmental&quot;</code> | 358 |
| <code>&quot;Personal and Household Services&quot;</code> | 342 |
| <code>&quot;Childcare&quot;</code> | 336 |
| <code>&quot;Trade and Services&quot;</code> | 333 |
| <code>&quot;Other&quot;</code> | 305 |
| <code>&quot;Commerce de détail&quot;</code> | 303 |
| <code>&quot;Human Resources&quot;</code> | 283 |
| <code>&quot;Entertainment&quot;</code> | 274 |
| <code>&quot;Servizi fiduciari/facility&quot;</code> | 266 |
| <code>&quot;Employment - Recruiting - Staffing&quot;</code> | 265 |
| <code>&quot;Transportation&quot;</code> | 263 |
| <code>&quot;Communications&quot;</code> | 261 |
| <code>&quot;Security and Surveillance&quot;</code> | 237 |
| <code>&quot;Legal&quot;</code> | 232 |
| <code>&quot;Oil &amp; Gas&quot;</code> | 229 |
| <code>&quot;Training&quot;</code> | 208 |
| <code>&quot;Informatique&quot;</code> | 202 |
| <code>&quot;Pharma&quot;</code> | 201 |
| <code>&quot;Pharma/Biotech/Clinical Research&quot;</code> | 201 |
| <code>&quot;Tecnología&quot;</code> | 201 |
| <code>&quot;Ospitalità&quot;</code> | 195 |
| <code>&quot;Airline - Aviation&quot;</code> | 193 |
| <code>&quot;Postos Prio&quot;</code> | 190 |
| <code>&quot;Design&quot;</code> | 189 |
| <code>&quot;Santé&quot;</code> | 189 |
| <code>&quot;Energy &amp; Power&quot;</code> | 186 |
| <code>&quot;Healthcare&quot;</code> | 186 |
| <code>&quot;Loisirs et sport&quot;</code> | 178 |
| <code>&quot;Ingénierie&quot;</code> | 174 |
| <code>&quot;Autre&quot;</code> | 173 |
| <code>&quot;Teknik&quot;</code> | 173 |
| <code>&quot;Restaurant/Food Services&quot;</code> | 172 |
| <code>&quot;Business Management&quot;</code> | 171 |
| <code>&quot;NGO (Public policy research)&quot;</code> | 170 |
| <code>&quot;Tecnologia&quot;</code> | 167 |
| <code>&quot;Entrepôt&quot;</code> | 166 |
| <code>&quot;Defence&quot;</code> | 165 |
| <code>&quot;Research &amp; Development&quot;</code> | 155 |
| <code>&quot;Research&quot;</code> | 144 |
| <code>&quot;Janitorial&quot;</code> | 140 |
| <code>&quot;Pharmaceutique / Pharmaceutical&quot;</code> | 139 |
| <code>&quot;Agriculture&quot;</code> | 136 |
| <code>&quot;Internet Services&quot;</code> | 125 |
| <code>&quot;Information Technology&quot;</code> | 124 |
| <code>&quot;Área 1&quot;</code> | 123 |
| <code>&quot;Sicurezza e sorveglianza&quot;</code> | 122 |
| <code>&quot;Electronics&quot;</code> | 121 |
| <code>&quot;Travel and Tourism&quot;</code> | 121 |
| <code>&quot;Security&quot;</code> | 120 |
| <code>&quot;Arts &amp; Graphics&quot;</code> | 119 |
| <code>&quot;Real Estate/Property Management&quot;</code> | 119 |
| <code>&quot;Ventes - Marketing&quot;</code> | 116 |
| <code>&quot;Retail &amp; Wholesale&quot;</code> | 114 |
| <code>&quot;Government &amp; Public Sector&quot;</code> | 113 |
| <code>&quot;Cleaning&quot;</code> | 110 |
| <code>&quot;Formation&quot;</code> | 110 |
| <code>&quot;Industrial&quot;</code> | 110 |
| <code>&quot;Research and Development&quot;</code> | 104 |
| <code>&quot;Services de restauration / alimentaires&quot;</code> | 103 |
| <code>&quot;Staffing/Employment Agencies&quot;</code> | 101 |
| <code>&quot;Computer&quot;</code> | 98 |
| <code>&quot;Translation and localization&quot;</code> | 98 |
| <code>&quot;Aerospace&quot;</code> | 97 |
| <code>&quot;Service à la clientèle&quot;</code> | 96 |
| <code>&quot;Railway&quot;</code> | 93 |
| <code>&quot;Financial Sector&quot;</code> | 92 |
| <code>&quot;コンサルタント業&quot;</code> | 92 |
| <code>&quot;Chemicals&quot;</code> | 91 |
| <code>&quot;Comptabilité&quot;</code> | 90 |
| <code>&quot;Réparation et maintenance&quot;</code> | 90 |
| <code>&quot;NGO&quot;</code> | 89 |
| <code>&quot;Installation&quot;</code> | 86 |
| <code>&quot;End User&quot;</code> | 84 |
| <code>&quot;Fintech&quot;</code> | 84 |
| <code>&quot;Faith Based Residential Recovery&quot;</code> | 82 |
| <code>&quot;Management&quot;</code> | 82 |
| <code>&quot;Livraison&quot;</code> | 81 |
| <code>&quot;ONLINE BETTING &amp; GAMBLING&quot;</code> | 81 |
| <code>&quot;Real Estate and Property&quot;</code> | 81 |
| <code>&quot;Repair / Maintenance Services&quot;</code> | 80 |
| <code>&quot;Services - Corporate B2B&quot;</code> | 79 |
| <code>&quot;Other/Not Classified&quot;</code> | 78 |
| <code>&quot;Property &amp; Real Estate&quot;</code> | 77 |
| <code>&quot;Property, Construction, Hospitality&quot;</code> | 77 |
| <code>&quot;Electronic Medical Records&quot;</code> | 76 |
| <code>&quot;Trasporto valori e gestione denaro&quot;</code> | 76 |
| <code>&quot;Ninguno&quot;</code> | 75 |
| <code>&quot;Landscaping&quot;</code> | 73 |
| <code>&quot;Transporte&quot;</code> | 73 |
| <code>&quot;Residential Facility&quot;</code> | 71 |
| <code>&quot;Restaurante/Servicios de alimentación&quot;</code> | 70 |
| <code>&quot;Travel&quot;</code> | 68 |
| <code>&quot;أخرى/غير مصنف&quot;</code> | 68 |
| <code>&quot;Pharmacie / Biotechnologie / Recherche clinique&quot;</code> | 66 |
| <code>&quot;Recruitment/Employment Firm&quot;</code> | 66 |
| <code>&quot;Exercise - Fitness&quot;</code> | 65 |
| <code>&quot;IT&quot;</code> | 65 |
| <code>&quot;Architecture et construction&quot;</code> | 64 |
| <code>&quot;Luxury Retail&quot;</code> | 63 |
| <code>&quot;Academic Jobs&quot;</code> | 62 |
| <code>&quot;Commercial Construction&quot;</code> | 62 |
| <code>&quot;Rental Services&quot;</code> | 62 |
| <code>&quot;Cosmetics&quot;</code> | 61 |
| <code>&quot;Sociale dienstverlening&quot;</code> | 60 |
| <code>&quot;Försvar&quot;</code> | 58 |
| <code>&quot;Ingénierie des matériaux&quot;</code> | 58 |
| <code>&quot;Operations&quot;</code> | 57 |
| <code>&quot;Skilling and Employment&quot;</code> | 57 |
| <code>&quot;Services financiers&quot;</code> | 56 |
| <code>&quot;HVAC&quot;</code> | 55 |
| <code>&quot;Hôtels et hébergement&quot;</code> | 53 |
| <code>&quot;Logistique&quot;</code> | 53 |
| <code>&quot;Software Development&quot;</code> | 53 |
| <code>&quot;Gestion d\\u2019entreprise&quot;</code> | 51 |
| <code>&quot;Cyber Security&quot;</code> | 49 |
| <code>&quot;Hair &amp; Beauty Salon&quot;</code> | 49 |
| <code>&quot;Onroerend goed&quot;</code> | 49 |
| <code>&quot;Asset and Wealth Management&quot;</code> | 48 |
| <code>&quot;Fashion&quot;</code> | 48 |
| <code>&quot;Printing/Packaging/Publishing&quot;</code> | 48 |
| <code>&quot;Electric Vehicles&quot;</code> | 47 |
| <code>&quot;Exploitation minière&quot;</code> | 47 |
| <code>&quot;IT Dienste&quot;</code> | 47 |
| <code>&quot;E-Commerce&quot;</code> | 46 |
| <code>&quot;ERA&quot;</code> | 46 |
| <code>&quot;Energy/Infrastructure&quot;</code> | 46 |
| <code>&quot;Gaming&quot;</code> | 46 |
| <code>&quot;Hotels and Lodging&quot;</code> | 46 |
| <code>&quot;Software Product&quot;</code> | 46 |
| <code>&quot;Industrie&quot;</code> | 45 |
| <code>&quot;Commerce électronique&quot;</code> | 44 |
| <code>&quot;Mental Healthcare&quot;</code> | 44 |
| <code>&quot;Pharmaceutique&quot;</code> | 44 |
| <code>&quot;Security/Law Enforcement&quot;</code> | 43 |
| <code>&quot;Hotéis e alojamentos&quot;</code> | 42 |
| <code>&quot;Sales&quot;</code> | 42 |
| <code>&quot;AEC&quot;</code> | 41 |
| <code>&quot;Accounting and Finance&quot;</code> | 41 |
| <code>&quot;Business Development&quot;</code> | 41 |
| <code>&quot;Electrical&quot;</code> | 41 |
| <code>&quot;Massage Therapist @ Google&quot;</code> | 41 |
| <code>&quot;Postos Shell&quot;</code> | 41 |
| <code>&quot;Manufacturier&quot;</code> | 40 |
| <code>&quot;Engineering Services&quot;</code> | 39 |
| <code>&quot;PROPERTY PRESERVATION FULL&quot;</code> | 39 |
| <code>&quot;Compliance&quot;</code> | 38 |
| <code>&quot;Recreation&quot;</code> | 38 |
| <code>&quot;Rooftop Solar&quot;</code> | 38 |
| <code>&quot;Tourism&quot;</code> | 38 |
| <code>&quot;E-commerce&quot;</code> | 37 |
| <code>&quot;Game Testing&quot;</code> | 37 |
| <code>&quot;Legal &amp; Compliance&quot;</code> | 37 |
| <code>&quot;Polymer / Plastic / Rubber&quot;</code> | 37 |
| <code>&quot;Administrative Jobs&quot;</code> | 36 |
| <code>&quot;Language Services&quot;</code> | 36 |
| <code>&quot;Waste Management&quot;</code> | 36 |
| <code>&quot;Autre/Non classifié&quot;</code> | 35 |
| <code>&quot;Ekonomi &amp; Redovisning&quot;</code> | 35 |
| <code>&quot;Non Profit Organization Management&quot;</code> | 35 |
| <code>&quot;Social Care&quot;</code> | 35 |
| <code>&quot;Sports Leisure &amp; Lifestyle&quot;</code> | 35 |
| <code>&quot;Textiles/Garments/Accessories&quot;</code> | 33 |
| <code>&quot;Bygg&quot;</code> | 32 |
| <code>&quot;Divertissement&quot;</code> | 32 |
| <code>&quot;Industri&quot;</code> | 32 |
| <code>&quot;Pulp &amp; Paper&quot;</code> | 32 |
| <code>&quot;SaaS&quot;</code> | 32 |
| <code>&quot;Sports and Physical Recreation&quot;</code> | 32 |
| <code>&quot;Automoción&quot;</code> | 31 |
| <code>&quot;Computer and Network Security&quot;</code> | 31 |
| <code>&quot;Energy and Infrastructure&quot;</code> | 31 |
| <code>&quot;Science &amp; Technology&quot;</code> | 31 |
| <code>&quot;Beratung&quot;</code> | 30 |
| <code>&quot;Environnement&quot;</code> | 30 |
| <code>&quot;Transports&quot;</code> | 30 |
| <code>&quot;Healthcare IT&quot;</code> | 29 |
| <code>&quot;Manufacturing, Engineering, Transportation &amp; Logistics&quot;</code> | 29 |
| <code>&quot;Quant Firms/HFT&quot;</code> | 29 |
| <code>&quot;Fire Protection&quot;</code> | 28 |
| <code>&quot;Gesundheitswesen&quot;</code> | 28 |
| <code>&quot;Public Sector and Government&quot;</code> | 28 |
| <code>&quot;BPO/ITES&quot;</code> | 27 |
| <code>&quot;Product&quot;</code> | 27 |
| <code>&quot;Cleaning Industry&quot;</code> | 26 |
| <code>&quot;Compagnie aérienne - Aviation&quot;</code> | 26 |
| <code>&quot;Public Accounting/CPA Firm&quot;</code> | 26 |
| <code>&quot;Public Health Research&quot;</code> | 26 |
| <code>&quot;Visual Effects&quot;</code> | 26 |
| <code>&quot;Anderes&quot;</code> | 25 |
| <code>&quot;Biotechnology&quot;</code> | 25 |
| <code>&quot;Escritórios&quot;</code> | 25 |
| <code>&quot;Immobilien-/Hausverwaltung&quot;</code> | 25 |
| <code>&quot;Mining&quot;</code> | 25 |
| <code>&quot;Production&quot;</code> | 25 |
| <code>&quot;Ristorazione&quot;</code> | 25 |
| <code>&quot;Immobilier&quot;</code> | 24 |
| <code>&quot;Public Relations&quot;</code> | 24 |
| <code>&quot;Renewable Energy&quot;</code> | 24 |
| <code>&quot;Vétérinaire&quot;</code> | 24 |
| <code>&quot;Wholesale Trade/Import-Export&quot;</code> | 24 |
| <code>&quot;Consumer&quot;</code> | 23 |
| <code>&quot;Dairy&quot;</code> | 23 |
| <code>&quot;Early Childhood Education &amp; Care&quot;</code> | 23 |
| <code>&quot;Energie und Versorgung&quot;</code> | 23 |
| <code>&quot;Finance&quot;</code> | 23 |
| <code>&quot;Event management&quot;</code> | 22 |
| <code>&quot;Massage Therapist&quot;</code> | 22 |
| <code>&quot;Mécanique&quot;</code> | 22 |
| <code>&quot;Ressources humaines&quot;</code> | 22 |
| <code>&quot;Organismes de bienfaisance sans but lucratif&quot;</code> | 21 |
| <code>&quot;Santé publique&quot;</code> | 21 |
| <code>&quot;تصدير/استيراد&quot;</code> | 21 |
| <code>&quot;Commercial and Industrial Refrigeration&quot;</code> | 20 |
| <code>&quot;Commercio e servizi&quot;</code> | 20 |
| <code>&quot;Fiscalité&quot;</code> | 20 |
| <code>&quot;Furniture&quot;</code> | 20 |
| <code>&quot;Gomma Plastica&quot;</code> | 20 |
| <code>&quot;Génie Civil&quot;</code> | 20 |
| <code>&quot;Information and Communication Technology&quot;</code> | 20 |
| <code>&quot;Mine Action Projects&quot;</code> | 20 |
| <code>&quot;Construcción&quot;</code> | 19 |
| <code>&quot;Education Administration Programmes&quot;</code> | 19 |
| <code>&quot;Fabrication&quot;</code> | 19 |
| <code>&quot;Géosciences&quot;</code> | 19 |
| <code>&quot;IT - Software Development&quot;</code> | 19 |
| <code>&quot;Seguros&quot;</code> | 19 |
| <code>&quot;Strategy and Planning&quot;</code> | 19 |
| <code>&quot;Technical Solutions &amp; IT Services&quot;</code> | 19 |
| <code>&quot;Technologie de l&#x27;Information&quot;</code> | 19 |
| <code>&quot;Adtech&quot;</code> | 18 |
| <code>&quot;Aircraft Leasing&quot;</code> | 18 |
| <code>&quot;Broking&quot;</code> | 18 |
| <code>&quot;Corporate Communication Consulting&quot;</code> | 18 |
| <code>&quot;Customer Experience&quot;</code> | 18 |
| <code>&quot;Event &amp; Conference&quot;</code> | 18 |
| <code>&quot;Geen&quot;</code> | 18 |
| <code>&quot;Semiconductor&quot;</code> | 18 |
| <code>&quot;Services sociaux&quot;</code> | 18 |
| <code>&quot;Servizi IT&quot;</code> | 18 |
| <code>&quot;Transport and Logistics&quot;</code> | 18 |
| <code>&quot;Web Development&quot;</code> | 18 |
| <code>&quot;Architektur und Konstruktion&quot;</code> | 17 |
| <code>&quot;Architettura ed edilizia&quot;</code> | 17 |
| <code>&quot;Educación&quot;</code> | 17 |
| <code>&quot;Gems &amp; Jewellery&quot;</code> | 17 |
| <code>&quot;ICT&quot;</code> | 17 |
| <code>&quot;Logistik&quot;</code> | 17 |
| <code>&quot;Services - B2B d\\u2019entreprise&quot;</code> | 17 |
| <code>&quot;Services de réparation / maintenance&quot;</code> | 17 |
| <code>&quot;Venture Capital&quot;</code> | 17 |
| <code>&quot;Broadcasting&quot;</code> | 16 |
| <code>&quot;Energi&quot;</code> | 16 |
| <code>&quot;Gestion&quot;</code> | 16 |
| <code>&quot;Global&quot;</code> | 16 |
| <code>&quot;Industriel&quot;</code> | 16 |
| <code>&quot;Ingenjörer&quot;</code> | 16 |
| <code>&quot;Private Credit &amp; Private Equity&quot;</code> | 16 |
| <code>&quot;Ressources Humaines&quot;</code> | 16 |
| <code>&quot;Services&quot;</code> | 16 |
| <code>&quot;Space Technology&quot;</code> | 16 |
| <code>&quot;Banque&quot;</code> | 15 |
| <code>&quot;Consultation &amp; Services&quot;</code> | 15 |
| <code>&quot;Marine&quot;</code> | 15 |
| <code>&quot;Supply &amp; Logistics&quot;</code> | 15 |
| <code>&quot;Uhren- &amp; Schmuckbranche&quot;</code> | 15 |
| <code>&quot;Utilities&quot;</code> | 15 |
| <code>&quot;Warehousing &amp; Supply Chain&quot;</code> | 15 |
| <code>&quot;Charity&quot;</code> | 14 |
| <code>&quot;Construction &amp; Mining&quot;</code> | 14 |
| <code>&quot;Costruzioni / Energy&quot;</code> | 14 |
| <code>&quot;Elektronik&quot;</code> | 14 |
| <code>&quot;Export/Import&quot;</code> | 14 |
| <code>&quot;FMCG&quot;</code> | 14 |
| <code>&quot;ITES&quot;</code> | 14 |
| <code>&quot;Identity Security&quot;</code> | 14 |
| <code>&quot;Logística&quot;</code> | 14 |
| <code>&quot;Outro&quot;</code> | 14 |
| <code>&quot;Plumbing&quot;</code> | 14 |
| <code>&quot;Quality&quot;</code> | 14 |
| <code>&quot;Science du bâtiment&quot;</code> | 14 |
| <code>&quot;Transport&quot;</code> | 14 |
| <code>&quot;Vendite - Marketing&quot;</code> | 14 |
| <code>&quot;Ventes&quot;</code> | 14 |
| <code>&quot;Éducation&quot;</code> | 14 |
| <code>&quot;Aerospace &amp; Defence&quot;</code> | 13 |
| <code>&quot;EdTech&quot;</code> | 13 |
| <code>&quot;Försäljning&quot;</code> | 13 |
| <code>&quot;Plumbing &amp; HVAC&quot;</code> | 13 |
| <code>&quot;Software&quot;</code> | 13 |
| <code>&quot;Student Success&quot;</code> | 13 |
| <code>&quot;EV&quot;</code> | 12 |
| <code>&quot;Fastigheter&quot;</code> | 12 |
| <code>&quot;Flygindustri&quot;</code> | 12 |
| <code>&quot;Hardware&quot;</code> | 12 |
| <code>&quot;Health&quot;</code> | 12 |
| <code>&quot;IT Consultancy&quot;</code> | 12 |
| <code>&quot;IT Professional Services&quot;</code> | 12 |
| <code>&quot;Industrial  Automation&quot;</code> | 12 |
| <code>&quot;Juridique&quot;</code> | 12 |
| <code>&quot;Maloprodaja&quot;</code> | 12 |
| <code>&quot;Metro&quot;</code> | 12 |
| <code>&quot;Service clientèle&quot;</code> | 12 |
| <code>&quot;Administración&quot;</code> | 11 |
| <code>&quot;Alfabet&quot;</code> | 11 |
| <code>&quot;Any Industry&quot;</code> | 11 |
| <code>&quot;Audio Video - Commercial&quot;</code> | 11 |
| <code>&quot;Business Solutions and Services&quot;</code> | 11 |
| <code>&quot;Comptabilité - Finance&quot;</code> | 11 |
| <code>&quot;Facility Management&quot;</code> | 11 |
| <code>&quot;Finance &amp; Accounts&quot;</code> | 11 |
| <code>&quot;Fordonsindustri&quot;</code> | 11 |
| <code>&quot;Hotel e sistemazione&quot;</code> | 11 |
| <code>&quot;IT Services and Consulting&quot;</code> | 11 |
| <code>&quot;Incline Village&quot;</code> | 11 |
| <code>&quot;Insurance and Technology&quot;</code> | 11 |
| <code>&quot;Internet Service&quot;</code> | 11 |
| <code>&quot;Internship Program&quot;</code> | 11 |
| <code>&quot;Laboratoire&quot;</code> | 11 |
| <code>&quot;Marketing &amp; Global Partnerships&quot;</code> | 11 |
| <code>&quot;Personnel d&#x27;éducation/Educational support staff&quot;</code> | 11 |
| <code>&quot;Robotics&quot;</code> | 11 |
| <code>&quot;Serviços Financeiros&quot;</code> | 11 |
| <code>&quot;Trauma Surgery&quot;</code> | 11 |
| <code>&quot;Vendas \\u2013 Marketing&quot;</code> | 11 |
| <code>&quot;Vente aux détails&quot;</code> | 11 |
| <code>&quot;Administração&quot;</code> | 10 |
| <code>&quot;Architecture, Delivery &amp; Leadership&quot;</code> | 10 |
| <code>&quot;Arts et graphismes&quot;</code> | 10 |
| <code>&quot;Building Automation&quot;</code> | 10 |
| <code>&quot;Creatives&quot;</code> | 10 |
| <code>&quot;Leisure and Sport&quot;</code> | 10 |
| <code>&quot;Manufacturing/Engineering&quot;</code> | 10 |
| <code>&quot;Maritime&quot;</code> | 10 |
| <code>&quot;Metals&quot;</code> | 10 |
| <code>&quot;Métallurgie&quot;</code> | 10 |
| <code>&quot;Product Management&quot;</code> | 10 |
| <code>&quot;Servizi di riparazione/Manutenzione&quot;</code> | 10 |
| <code>&quot;Siderometalurgia&quot;</code> | 10 |
| <code>&quot;Social Enterprise&quot;</code> | 10 |
| <code>&quot;Translation &amp; Localization&quot;</code> | 10 |
| <code>&quot;Wealth Management&quot;</code> | 10 |
| <code>&quot;1. Teaching _  General Specialization (School /College)&quot;</code> | 9 |
| <code>&quot;Administratif&quot;</code> | 9 |
| <code>&quot;Amministrazione&quot;</code> | 9 |
| <code>&quot;Amministrazione e settore pubblico&quot;</code> | 9 |
| <code>&quot;Animation&quot;</code> | 9 |
| <code>&quot;Comércio e serviços&quot;</code> | 9 |
| <code>&quot;Cuisine&quot;</code> | 9 |
| <code>&quot;Enfance, famille&quot;</code> | 9 |
| <code>&quot;Fabrication générale&quot;</code> | 9 |
| <code>&quot;Formazione&quot;</code> | 9 |
| <code>&quot;Géophysique&quot;</code> | 9 |
| <code>&quot;Horticulture&quot;</code> | 9 |
| <code>&quot;Import - Export&quot;</code> | 9 |
| <code>&quot;Payments / FinTech&quot;</code> | 9 |
| <code>&quot;Water Treatment / Waste Management&quot;</code> | 9 |
| <code>&quot;Accounting &amp; Finance&quot;</code> | 8 |
| <code>&quot;Assurances&quot;</code> | 8 |
| <code>&quot;Catering&quot;</code> | 8 |
| <code>&quot;Construction / Building&quot;</code> | 8 |
| <code>&quot;Cybersecurity&quot;</code> | 8 |
| <code>&quot;Growth Equity Investment Fund&quot;</code> | 8 |
| <code>&quot;Inne/nieklasyfikowane&quot;</code> | 8 |
| <code>&quot;Interior / Furniture&quot;</code> | 8 |
| <code>&quot;Médical&quot;</code> | 8 |
| <code>&quot;Pet Evolution&quot;</code> | 8 |
| <code>&quot;Retail/Fashion&quot;</code> | 8 |
| <code>&quot;Sales Operations&quot;</code> | 8 |
| <code>&quot;Technical&quot;</code> | 8 |
| <code>&quot;Telecomunicaciones&quot;</code> | 8 |
| <code>&quot;Énergie et services publics&quot;</code> | 8 |
| <code>&quot;3. Teaching _ Engineering /Arts &amp; Science College&quot;</code> | 7 |
| <code>&quot;Academics&quot;</code> | 7 |
| <code>&quot;Business Intelligence&quot;</code> | 7 |
| <code>&quot;Cannabis Testing&quot;</code> | 7 |
| <code>&quot;Comunicazioni&quot;</code> | 7 |
| <code>&quot;Construction - Full Time/Per Diem&quot;</code> | 7 |
| <code>&quot;Corporate Affairs &amp; Compliances&quot;</code> | 7 |
| <code>&quot;Corporate Sales&quot;</code> | 7 |
| <code>&quot;Desarrollo de Software&quot;</code> | 7 |
| <code>&quot;E-Publishing&quot;</code> | 7 |
| <code>&quot;Education et jeunesse&quot;</code> | 7 |
| <code>&quot;Entretien&quot;</code> | 7 |
| <code>&quot;FinTech&quot;</code> | 7 |
| <code>&quot;Finance &amp; Billing&quot;</code> | 7 |
| <code>&quot;Géoenvironnement&quot;</code> | 7 |
| <code>&quot;Géotechnique&quot;</code> | 7 |
| <code>&quot;IT-services&quot;</code> | 7 |
| <code>&quot;Investment Banking&quot;</code> | 7 |
| <code>&quot;Logistica&quot;</code> | 7 |
| <code>&quot;Management Consulting&quot;</code> | 7 |
| <code>&quot;Merchandising&quot;</code> | 7 |
| <code>&quot;Payment Processing&quot;</code> | 7 |
| <code>&quot;Produits alimentaires&quot;</code> | 7 |
| <code>&quot;Project Management&quot;</code> | 7 |
| <code>&quot;Revenue Sales&quot;</code> | 7 |
| <code>&quot;Serviços de reparo/manutenção&quot;</code> | 7 |
| <code>&quot;Soins infirmiers&quot;</code> | 7 |
| <code>&quot;UI Developer&quot;</code> | 7 |
| <code>&quot;Voirie et infrastructures&quot;</code> | 7 |
| <code>&quot;Anläggning&quot;</code> | 6 |
| <code>&quot;Automation&quot;</code> | 6 |
| <code>&quot;BTP&quot;</code> | 6 |
| <code>&quot;Banca&quot;</code> | 6 |
| <code>&quot;Conseil&quot;</code> | 6 |
| <code>&quot;Contabilidade&quot;</code> | 6 |
| <code>&quot;Corporate Finance&quot;</code> | 6 |
| <code>&quot;Creative Media Production&quot;</code> | 6 |
| <code>&quot;Cyber Security &amp; IT&quot;</code> | 6 |
| <code>&quot;Digital&quot;</code> | 6 |
| <code>&quot;ERA Rental&quot;</code> | 6 |
| <code>&quot;Equipe transverse&quot;</code> | 6 |
| <code>&quot;Finance &amp; Strategy&quot;</code> | 6 |
| <code>&quot;Finances&quot;</code> | 6 |
| <code>&quot;Finanziell Dienste&quot;</code> | 6 |
| <code>&quot;Försäljning B2B&quot;</code> | 6 |
| <code>&quot;Game Development&quot;</code> | 6 |
| <code>&quot;IT Support&quot;</code> | 6 |
| <code>&quot;Industria&quot;</code> | 6 |
| <code>&quot;Not in use&quot;</code> | 6 |
| <code>&quot;Orthopedic Surgery&quot;</code> | 6 |
| <code>&quot;PetRehomer Volunteer Openings&quot;</code> | 6 |
| <code>&quot;Placements&quot;</code> | 6 |
| <code>&quot;Prodaja&quot;</code> | 6 |
| <code>&quot;SAP Commerce Cloud (hybris)&quot;</code> | 6 |
| <code>&quot;Semiconductor and New &amp; Emerging Opportunities&quot;</code> | 6 |
| <code>&quot;Services \\u2013 Firmenkundengeschäfte&quot;</code> | 6 |
| <code>&quot;Services à la personne&quot;</code> | 6 |
| <code>&quot;Servizi finanziari&quot;</code> | 6 |
| <code>&quot;Solar power&quot;</code> | 6 |
| <code>&quot;Teamer:in Sommercamp&quot;</code> | 6 |
| <code>&quot;Unternehmensberatung Sparkassen&quot;</code> | 6 |
| <code>&quot;Vertrieb \\u2013 Marketing&quot;</code> | 6 |
| <code>&quot;المبيعات - التسويق&quot;</code> | 6 |
| <code>&quot;6. Admin &amp; Support Functions&quot;</code> | 5 |
| <code>&quot;Achats - Approvisionnement&quot;</code> | 5 |
| <code>&quot;Administration générale&quot;</code> | 5 |
| <code>&quot;Alimentari&quot;</code> | 5 |
| <code>&quot;Architecture, bâtiment&quot;</code> | 5 |
| <code>&quot;Artificial Intelligence  (AI) &amp; Analytics&quot;</code> | 5 |
| <code>&quot;Artificial Intelligence (AI)&quot;</code> | 5 |
| <code>&quot;BFSI&quot;</code> | 5 |
| <code>&quot;Client Support&quot;</code> | 5 |
| <code>&quot;Commerce et services&quot;</code> | 5 |
| <code>&quot;Comunicaciones&quot;</code> | 5 |
| <code>&quot;Customer Support&quot;</code> | 5 |
| <code>&quot;Digital Lab&quot;</code> | 5 |
| <code>&quot;Field Service&quot;</code> | 5 |
| <code>&quot;Fin Tech&quot;</code> | 5 |
| <code>&quot;Finance - Comptabilité&quot;</code> | 5 |
| <code>&quot;GreenTech&quot;</code> | 5 |
| <code>&quot;IT サービス業&quot;</code> | 5 |
| <code>&quot;Identity Security - Delivery&quot;</code> | 5 |
| <code>&quot;Industry&quot;</code> | 5 |
| <code>&quot;Logistika&quot;</code> | 5 |
| <code>&quot;Mechanical&quot;</code> | 5 |
| <code>&quot;NBFC&quot;</code> | 5 |
| <code>&quot;Neurosurgery&quot;</code> | 5 |
| <code>&quot;Personnel enseignant/Teaching staff&quot;</code> | 5 |
| <code>&quot;Producer&quot;</code> | 5 |
| <code>&quot;Projects&quot;</code> | 5 |
| <code>&quot;Quality assurance (QA)&quot;</code> | 5 |
| <code>&quot;Recursos humanos&quot;</code> | 5 |
| <code>&quot;Servicio de transporte de mercancía&quot;</code> | 5 |
| <code>&quot;Serviços financeiros&quot;</code> | 5 |
| <code>&quot;Shipping/Marine&quot;</code> | 5 |
| <code>&quot;Summer Language Courses&quot;</code> | 5 |
| <code>&quot;Supply&quot;</code> | 5 |
| <code>&quot;Säkerhet &amp; övervakning&quot;</code> | 5 |
| <code>&quot;Telekommunikation&quot;</code> | 5 |
| <code>&quot;UGOSTITELJSTVO&quot;</code> | 5 |
| <code>&quot;Usługi IT&quot;</code> | 5 |
| <code>&quot;Weitere Begleitung&quot;</code> | 5 |
| <code>&quot;2. Teaching _  Languages&quot;</code> | 4 |
| <code>&quot;2D&quot;</code> | 4 |
| <code>&quot;4. Teaching _ Co Curricular&quot;</code> | 4 |
| <code>&quot;7. Construction &amp; Facility Maintenance&quot;</code> | 4 |
| <code>&quot;Agricultura&quot;</code> | 4 |
| <code>&quot;Biens et Immobilier&quot;</code> | 4 |
| <code>&quot;Bilgi Teknolojisi&quot;</code> | 4 |
| <code>&quot;Boston Training Academy&quot;</code> | 4 |
| <code>&quot;Cariste&quot;</code> | 4 |
| <code>&quot;Chauffage, ventilation et climatisation&quot;</code> | 4 |
| <code>&quot;Computer Software&quot;</code> | 4 |
| <code>&quot;Concrete&quot;</code> | 4 |
| <code>&quot;Construção&quot;</code> | 4 |
| <code>&quot;Digital Transformation&quot;</code> | 4 |
| <code>&quot;Digital marketing&quot;</code> | 4 |
| <code>&quot;Département financier&quot;</code> | 4 |
| <code>&quot;EMS&quot;</code> | 4 |
| <code>&quot;Educação&quot;</code> | 4 |
| <code>&quot;Emploi - Recrutement - Dotation en personnel&quot;</code> | 4 |
| <code>&quot;Energy &amp; Utilities&quot;</code> | 4 |
| <code>&quot;Enterprise Sales&quot;</code> | 4 |
| <code>&quot;Expert Witness&quot;</code> | 4 |
| <code>&quot;Fertilizers/Pesticides&quot;</code> | 4 |
| <code>&quot;Gifting&quot;</code> | 4 |
| <code>&quot;HR&quot;</code> | 4 |
| <code>&quot;Hospitality for Client&quot;</code> | 4 |
| <code>&quot;Hôtellerie&quot;</code> | 4 |
| <code>&quot;IT Product Software&quot;</code> | 4 |
| <code>&quot;In der ambulanten Alltagsbegleitung&quot;</code> | 4 |
| <code>&quot;Industrial Automation&quot;</code> | 4 |
| <code>&quot;Informatique &amp; Technologies&quot;</code> | 4 |
| <code>&quot;Infrastructure projects&quot;</code> | 4 |
| <code>&quot;Instructor&quot;</code> | 4 |
| <code>&quot;Inter-governmental Organisation&quot;</code> | 4 |
| <code>&quot;International Trade&quot;</code> | 4 |
| <code>&quot;Internetdienste&quot;</code> | 4 |
| <code>&quot;Java Developer&quot;</code> | 4 |
| <code>&quot;Legal Technology&quot;</code> | 4 |
| <code>&quot;Marchandisage&quot;</code> | 4 |
| <code>&quot;Marketing &amp; Sales&quot;</code> | 4 |
| <code>&quot;Metalle&quot;</code> | 4 |
| <code>&quot;Network Infrastructure&quot;</code> | 4 |
| <code>&quot;Non Profit&quot;</code> | 4 |
| <code>&quot;Parking&quot;</code> | 4 |
| <code>&quot;Power Transformer Manufacturing&quot;</code> | 4 |
| <code>&quot;Produits cosmétiques&quot;</code> | 4 |
| <code>&quot;Restauration&quot;</code> | 4 |
| <code>&quot;Sales Development&quot;</code> | 4 |
| <code>&quot;Serviços de reparação/manutenção&quot;</code> | 4 |
| <code>&quot;Sécurité et surveillance&quot;</code> | 4 |
| <code>&quot;TI&quot;</code> | 4 |
| <code>&quot;Technique&quot;</code> | 4 |
| <code>&quot;Tessile/Indumenti/Accessori&quot;</code> | 4 |
| <code>&quot;Tillverkning&quot;</code> | 4 |
| <code>&quot;Veleprodajna trgovina/Uvoz-Izvoz&quot;</code> | 4 |
| <code>&quot;Actuariat&quot;</code> | 3 |
| <code>&quot;Administrative&quot;</code> | 3 |
| <code>&quot;Advertising and Marketing&quot;</code> | 3 |
| <code>&quot;Any&quot;</code> | 3 |
| <code>&quot;Arti e grafica&quot;</code> | 3 |
| <code>&quot;Artificial Intelligence&quot;</code> | 3 |
| <code>&quot;Beni di largo consumo/Cibi/Bevande&quot;</code> | 3 |
| <code>&quot;Business Operations&quot;</code> | 3 |
| <code>&quot;CG&quot;</code> | 3 |
| <code>&quot;Center for Resilience Strategies&quot;</code> | 3 |
| <code>&quot;Comercial&quot;</code> | 3 |
| <code>&quot;Commercial, vente&quot;</code> | 3 |
| <code>&quot;Community-Based Employment &amp; Vocational Training Services&quot;</code> | 3 |
| <code>&quot;Consommation&quot;</code> | 3 |
| <code>&quot;Construction Inspection&quot;</code> | 3 |
| <code>&quot;Construction Management&quot;</code> | 3 |
| <code>&quot;Consultoria&quot;</code> | 3 |
| <code>&quot;Consultoría&quot;</code> | 3 |
| <code>&quot;Costruzione&quot;</code> | 3 |
| <code>&quot;Customer Care&quot;</code> | 3 |
| <code>&quot;Customer Services&quot;</code> | 3 |
| <code>&quot;Data Analytics &amp; Research&quot;</code> | 3 |
| <code>&quot;E Commerce&quot;</code> | 3 |
| <code>&quot;E-Learning Providers&quot;</code> | 3 |
| <code>&quot;Energia e servizi&quot;</code> | 3 |
| <code>&quot;Eventos&quot;</code> | 3 |
| <code>&quot;Forages géotechniques et environnementaux&quot;</code> | 3 |
| <code>&quot;Grocery&quot;</code> | 3 |
| <code>&quot;Horticultural Sales&quot;</code> | 3 |
| <code>&quot;Hotels und Unterkunft&quot;</code> | 3 |
| <code>&quot;Human Resource&quot;</code> | 3 |
| <code>&quot;Image Processing&quot;</code> | 3 |
| <code>&quot;Ingeniería&quot;</code> | 3 |
| <code>&quot;Intellectual property&quot;</code> | 3 |
| <code>&quot;Konsulttjänster&quot;</code> | 3 |
| <code>&quot;Konsumgüter/Lebensmittel/Getränke&quot;</code> | 3 |
| <code>&quot;Litigation &amp; ADR&quot;</code> | 3 |
| <code>&quot;Maintenance&quot;</code> | 3 |
| <code>&quot;Medical Device&quot;</code> | 3 |
| <code>&quot;Medizin&quot;</code> | 3 |
| <code>&quot;Mortgage&quot;</code> | 3 |
| <code>&quot;Métaux&quot;</code> | 3 |
| <code>&quot;Peaks Recovery Center&quot;</code> | 3 |
| <code>&quot;Pet Store&quot;</code> | 3 |
| <code>&quot;Project&quot;</code> | 3 |
| <code>&quot;Property Fit-out&quot;</code> | 3 |
| <code>&quot;Publicité&quot;</code> | 3 |
| <code>&quot;Restaurants/Lebensmittelservices&quot;</code> | 3 |
| <code>&quot;Risk and Compliance&quot;</code> | 3 |
| <code>&quot;Servicios de TI&quot;</code> | 3 |
| <code>&quot;Serviços TI&quot;</code> | 3 |
| <code>&quot;Serviços de TI&quot;</code> | 3 |
| <code>&quot;Strategy &amp; Planning&quot;</code> | 3 |
| <code>&quot;Syndic&quot;</code> | 3 |
| <code>&quot;Systems Engineering&quot;</code> | 3 |
| <code>&quot;Technical Support &amp; Customer Services&quot;</code> | 3 |
| <code>&quot;Teknoloji&quot;</code> | 3 |
| <code>&quot;Tele Communication&quot;</code> | 3 |
| <code>&quot;Trasporti&quot;</code> | 3 |
| <code>&quot;UPM Mechanical&quot;</code> | 3 |
| <code>&quot;VVS&quot;</code> | 3 |
| <code>&quot;Venture Capital - Investments&quot;</code> | 3 |
| <code>&quot;Warehouse/Logistics&quot;</code> | 3 |
| <code>&quot;الإدارة&quot;</code> | 3 |
| <code>&quot;التكنولوجيا&quot;</code> | 3 |
| <code>&quot;الرعاية الصحية&quot;</code> | 3 |
| <code>&quot;الموارد البشرية&quot;</code> | 3 |
| <code>&quot;خدمات الإصلاح / الصيانة&quot;</code> | 3 |
| <code>&quot;5. Training &amp; Placements&quot;</code> | 2 |
| <code>&quot;8.  Admissions &amp; Marketing&quot;</code> | 2 |
| <code>&quot;Account Management&quot;</code> | 2 |
| <code>&quot;Administration de réseaux / système&quot;</code> | 2 |
| <code>&quot;AgriTech&quot;</code> | 2 |
| <code>&quot;Almacén y Logística&quot;</code> | 2 |
| <code>&quot;Arkitektur&quot;</code> | 2 |
| <code>&quot;Assurance&quot;</code> | 2 |
| <code>&quot;Assurance qualité&quot;</code> | 2 |
| <code>&quot;Ausbildung&quot;</code> | 2 |
| <code>&quot;Automotive and Next Generation Technology&quot;</code> | 2 |
| <code>&quot;Avfallshantering&quot;</code> | 2 |
| <code>&quot;Buchhaltung&quot;</code> | 2 |
| <code>&quot;Business Analyst&quot;</code> | 2 |
| <code>&quot;Business Support&quot;</code> | 2 |
| <code>&quot;CA Firm&quot;</code> | 2 |
| <code>&quot;CEO&#x27;s Office&quot;</code> | 2 |
| <code>&quot;CYB Human Resources&quot;</code> | 2 |
| <code>&quot;Citoyenneté, population&quot;</code> | 2 |
| <code>&quot;Clinical Home Health Care&quot;</code> | 2 |
| <code>&quot;Cognus&quot;</code> | 2 |
| <code>&quot;Community Care&quot;</code> | 2 |
| <code>&quot;Comptabilité &amp; Finance&quot;</code> | 2 |
| <code>&quot;Comptes stratégiques&quot;</code> | 2 |
| <code>&quot;Comunicações&quot;</code> | 2 |
| <code>&quot;Consumer Operations&quot;</code> | 2 |
| <code>&quot;Consumer Sales&quot;</code> | 2 |
| <code>&quot;Contrôle Accès-Fermeture&quot;</code> | 2 |
| <code>&quot;Courses&quot;</code> | 2 |
| <code>&quot;Culture&quot;</code> | 2 |
| <code>&quot;Customer Activation&quot;</code> | 2 |
| <code>&quot;Customer Success  &amp; Support&quot;</code> | 2 |
| <code>&quot;Development&quot;</code> | 2 |
| <code>&quot;Digital financial services&quot;</code> | 2 |
| <code>&quot;Direkcija&quot;</code> | 2 |
| <code>&quot;Dév. économique&quot;</code> | 2 |
| <code>&quot;Développement  Web&quot;</code> | 2 |
| <code>&quot;Ed-Tech&quot;</code> | 2 |
| <code>&quot;Einzelhandel&quot;</code> | 2 |
| <code>&quot;Electromechanical services&quot;</code> | 2 |
| <code>&quot;Energy&quot;</code> | 2 |
| <code>&quot;Engenharia&quot;</code> | 2 |
| <code>&quot;Environmental/PFAS Testing&quot;</code> | 2 |
| <code>&quot;Event Management&quot;</code> | 2 |
| <code>&quot;Financial technology&quot;</code> | 2 |
| <code>&quot;Financiero&quot;</code> | 2 |
| <code>&quot;Game Design&quot;</code> | 2 |
| <code>&quot;Gaming Casino&quot;</code> | 2 |
| <code>&quot;Gestion immobilière / des biens&quot;</code> | 2 |
| <code>&quot;Gestione&quot;</code> | 2 |
| <code>&quot;Grants &amp; Incentives&quot;</code> | 2 |
| <code>&quot;Habitat&quot;</code> | 2 |
| <code>&quot;Handel und Services&quot;</code> | 2 |
| <code>&quot;Herstellung&quot;</code> | 2 |
| <code>&quot;Hotel &amp; Tourism&quot;</code> | 2 |
| <code>&quot;IT Products&quot;</code> | 2 |
| <code>&quot;Inclusion sociale&quot;</code> | 2 |
| <code>&quot;Infant Care&quot;</code> | 2 |
| <code>&quot;Information Communications &amp; Technology&quot;</code> | 2 |
| <code>&quot;Information Technology and Services&quot;</code> | 2 |
| <code>&quot;Instalações industriais&quot;</code> | 2 |
| <code>&quot;Internal Audit&quot;</code> | 2 |
| <code>&quot;Kundendienst&quot;</code> | 2 |
| <code>&quot;Kundtjänst&quot;</code> | 2 |
| <code>&quot;Las Vegas&quot;</code> | 2 |
| <code>&quot;Lebensmittel&quot;</code> | 2 |
| <code>&quot;Legal Process Outsourcing&quot;</code> | 2 |
| <code>&quot;Lubricant Sales&quot;</code> | 2 |
| <code>&quot;M&amp;A and Transactions&quot;</code> | 2 |
| <code>&quot;Managed Campaigns&quot;</code> | 2 |
| <code>&quot;Matchmaking / Matrimonial Service&quot;</code> | 2 |
| <code>&quot;Motion Pictures and Film&quot;</code> | 2 |
| <code>&quot;Médias&quot;</code> | 2 |
| <code>&quot;Médias, Rédaction Arabophone&quot;</code> | 2 |
| <code>&quot;NON PROFIT ORGANIZATION&quot;</code> | 2 |
| <code>&quot;Nonprofit - entrepreneurial support&quot;</code> | 2 |
| <code>&quot;ONG / Services sociaux&quot;</code> | 2 |
| <code>&quot;Organisme de bienfaisance&quot;</code> | 2 |
| <code>&quot;Others&quot;</code> | 2 |
| <code>&quot;PEP - People Empowerment Platform&quot;</code> | 2 |
| <code>&quot;Paper&quot;</code> | 2 |
| <code>&quot;Pipeline&quot;</code> | 2 |
| <code>&quot;Procurement&quot;</code> | 2 |
| <code>&quot;Professional Services&quot;</code> | 2 |
| <code>&quot;Professional services&quot;</code> | 2 |
| <code>&quot;Pétrole et gaz&quot;</code> | 2 |
| <code>&quot;Radiodiffusion&quot;</code> | 2 |
| <code>&quot;Real Time&quot;</code> | 2 |
| <code>&quot;Repair &amp; Maintenance&quot;</code> | 2 |
| <code>&quot;Reparaturen/Wartungsdienste&quot;</code> | 2 |
| <code>&quot;Residential Construction&quot;</code> | 2 |
| <code>&quot;Restauration collective&quot;</code> | 2 |
| <code>&quot;Retalho&quot;</code> | 2 |
| <code>&quot;Servizi personali e domestici&quot;</code> | 2 |
| <code>&quot;Servizio clienti&quot;</code> | 2 |
| <code>&quot;Social Media&quot;</code> | 2 |
| <code>&quot;Software Engg.&quot;</code> | 2 |
| <code>&quot;Soins&quot;</code> | 2 |
| <code>&quot;Sonstiges/Nicht klassifiziert&quot;</code> | 2 |
| <code>&quot;Strategy&quot;</code> | 2 |
| <code>&quot;Swissnex in India&quot;</code> | 2 |
| <code>&quot;Syndica&quot;</code> | 2 |
| <code>&quot;Telecom Voice/SMS&quot;</code> | 2 |
| <code>&quot;Temporary Jobs&quot;</code> | 2 |
| <code>&quot;Thrift Store&quot;</code> | 2 |
| <code>&quot;Training and Placement&quot;</code> | 2 |
| <code>&quot;Trgovina i usluge&quot;</code> | 2 |
| <code>&quot;Télécommunications&quot;</code> | 2 |
| <code>&quot;Vendas - marketing&quot;</code> | 2 |
| <code>&quot;Ventas y marketing&quot;</code> | 2 |
| <code>&quot;Webdesign&quot;</code> | 2 |
| <code>&quot;Werben&quot;</code> | 2 |
| <code>&quot;produzione industriale&quot;</code> | 2 |
| <code>&quot;theFace HR&quot;</code> | 2 |
| <code>&quot;Építészet és építőipar&quot;</code> | 2 |
| <code>&quot;الخدمات - شركات B2B&quot;</code> | 2 |
| <code>&quot;خدمة العملاء&quot;</code> | 2 |
| <code>&quot;その他&quot;</code> | 2 |
| <code>&quot;AI&quot;</code> | 1 |
| <code>&quot;AI &amp; Automation&quot;</code> | 1 |
| <code>&quot;AI Medical Software&quot;</code> | 1 |
| <code>&quot;AI Research&quot;</code> | 1 |
| <code>&quot;Accounting (USA)&quot;</code> | 1 |
| <code>&quot;Accounts (Maritime)&quot;</code> | 1 |
| <code>&quot;Achats&quot;</code> | 1 |
| <code>&quot;Admin &amp; Support&quot;</code> | 1 |
| <code>&quot;Administración, Contabilidad y Finanzas&quot;</code> | 1 |
| <code>&quot;Administratie&quot;</code> | 1 |
| <code>&quot;Administrative Services&quot;</code> | 1 |
| <code>&quot;Aeronáutico&quot;</code> | 1 |
| <code>&quot;Aerospace and Aviation&quot;</code> | 1 |
| <code>&quot;Ag de communication&quot;</code> | 1 |
| <code>&quot;Agences de recrutement / d\\u2019emploi&quot;</code> | 1 |
| <code>&quot;Agency Workers&quot;</code> | 1 |
| <code>&quot;Agri&quot;</code> | 1 |
| <code>&quot;Algemeen&quot;</code> | 1 |
| <code>&quot;Altri&quot;</code> | 1 |
| <code>&quot;Altro/Non classificato&quot;</code> | 1 |
| <code>&quot;Ambiental&quot;</code> | 1 |
| <code>&quot;Anlagenmechaniker&quot;</code> | 1 |
| <code>&quot;Architecture/Design&quot;</code> | 1 |
| <code>&quot;Art Department&quot;</code> | 1 |
| <code>&quot;Assicurazione&quot;</code> | 1 |
| <code>&quot;Audit&quot;</code> | 1 |
| <code>&quot;Audit, Advisory and Tax&quot;</code> | 1 |
| <code>&quot;Automobile&quot;</code> | 1 |
| <code>&quot;Automóvel&quot;</code> | 1 |
| <code>&quot;Autonomie&quot;</code> | 1 |
| <code>&quot;Autres / Non classifiés&quot;</code> | 1 |
| <code>&quot;BTP &amp; second oeuvre&quot;</code> | 1 |
| <code>&quot;Back Office&quot;</code> | 1 |
| <code>&quot;Bancario&quot;</code> | 1 |
| <code>&quot;Banking and Financial Services&quot;</code> | 1 |
| <code>&quot;Banking, Financial Service &amp; Insurance&quot;</code> | 1 |
| <code>&quot;Banking, Financial Services &amp; Insurance&quot;</code> | 1 |
| <code>&quot;Beauty/ Personal Care&quot;</code> | 1 |
| <code>&quot;Beschäftigung \\u2013 Personalwerbung \\u2013 Personalvermittlung&quot;</code> | 1 |
| <code>&quot;Bildung&quot;</code> | 1 |
| <code>&quot;Bioteknik&quot;</code> | 1 |
| <code>&quot;Bois / Fibre / Papier&quot;</code> | 1 |
| <code>&quot;Building Management System&quot;</code> | 1 |
| <code>&quot;Bureau de projets&quot;</code> | 1 |
| <code>&quot;Bureautique&quot;</code> | 1 |
| <code>&quot;Cabinet audit &amp; expertise&quot;</code> | 1 |
| <code>&quot;Calidad de Software&quot;</code> | 1 |
| <code>&quot;Candidatura Espontânea&quot;</code> | 1 |
| <code>&quot;Careers at STAFFED INC.&quot;</code> | 1 |
| <code>&quot;Cartel Coffee&quot;</code> | 1 |
| <code>&quot;Centro Recreativo&quot;</code> | 1 |
| <code>&quot;Certification &amp; Inspections&quot;</code> | 1 |
| <code>&quot;Chemicals, Materials &amp; Food&quot;</code> | 1 |
| <code>&quot;Comercio y servicios&quot;</code> | 1 |
| <code>&quot;Commerce de détail et de gros&quot;</code> | 1 |
| <code>&quot;Commercial&quot;</code> | 1 |
| <code>&quot;Communications, Media &amp; Entertainment&quot;</code> | 1 |
| <code>&quot;Conception des systèmes de régulation / Technical Conception and Drawing&quot;</code> | 1 |
| <code>&quot;Construction - Electrical&quot;</code> | 1 |
| <code>&quot;Construction / Engineering / Infrastructure / Cement / Metal&quot;</code> | 1 |
| <code>&quot;Consulenza&quot;</code> | 1 |
| <code>&quot;Consultancy&quot;</code> | 1 |
| <code>&quot;Consulting Services&quot;</code> | 1 |
| <code>&quot;Consumer Channel&quot;</code> | 1 |
| <code>&quot;Consumer Customer Retentions&quot;</code> | 1 |
| <code>&quot;Consumer Systems&quot;</code> | 1 |
| <code>&quot;Contabilità&quot;</code> | 1 |
| <code>&quot;Content&quot;</code> | 1 |
| <code>&quot;Creative&quot;</code> | 1 |
| <code>&quot;Creative Services&quot;</code> | 1 |
| <code>&quot;Customer Success&quot;</code> | 1 |
| <code>&quot;Data&quot;</code> | 1 |
| <code>&quot;Dental Billing Industry&quot;</code> | 1 |
| <code>&quot;Denver Metro Security Inc.&quot;</code> | 1 |
| <code>&quot;Digital Health&quot;</code> | 1 |
| <code>&quot;Digital Marketing&quot;</code> | 1 |
| <code>&quot;Développement des affaires&quot;</code> | 1 |
| <code>&quot;E-learning &amp; EdTech&quot;</code> | 1 |
| <code>&quot;ESN&quot;</code> | 1 |
| <code>&quot;ESTETISTA&quot;</code> | 1 |
| <code>&quot;Egyéb&quot;</code> | 1 |
| <code>&quot;Electrical Inspection&quot;</code> | 1 |
| <code>&quot;Electrónica&quot;</code> | 1 |
| <code>&quot;Emerging &amp; Niche Tech&quot;</code> | 1 |
| <code>&quot;Empfang&quot;</code> | 1 |
| <code>&quot;Energie et climat&quot;</code> | 1 |
| <code>&quot;Energía y servicios públicos&quot;</code> | 1 |
| <code>&quot;Entreprise de recrutement / d\\u2019emploi&quot;</code> | 1 |
| <code>&quot;Entretien des bâtiments&quot;</code> | 1 |
| <code>&quot;Equity Research&quot;</code> | 1 |
| <code>&quot;Ergotherapie&quot;</code> | 1 |
| <code>&quot;Estimating&quot;</code> | 1 |
| <code>&quot;Estágio&quot;</code> | 1 |
| <code>&quot;Events Services&quot;</code> | 1 |
| <code>&quot;FX&quot;</code> | 1 |
| <code>&quot;Farmacia/Biotecnología/Investigación clínica&quot;</code> | 1 |
| <code>&quot;Farmacija&quot;</code> | 1 |
| <code>&quot;Finance and Insurance&quot;</code> | 1 |
| <code>&quot;Financiële diensten&quot;</code> | 1 |
| <code>&quot;Forschung und Entwicklung&quot;</code> | 1 |
| <code>&quot;Fußpflege&quot;</code> | 1 |
| <code>&quot;Gas&quot;</code> | 1 |
| <code>&quot;General&quot;</code> | 1 |
| <code>&quot;General Volunteer Application Form&quot;</code> | 1 |
| <code>&quot;Generative&quot;</code> | 1 |
| <code>&quot;Gestion de stocks, entrepôt / Inventory Management, Warehouse&quot;</code> | 1 |
| <code>&quot;Gestion, comptabilité, finance&quot;</code> | 1 |
| <code>&quot;Gestione aziendale&quot;</code> | 1 |
| <code>&quot;Gestão&quot;</code> | 1 |
| <code>&quot;Government&quot;</code> | 1 |
| <code>&quot;Growth&quot;</code> | 1 |
| <code>&quot;Génie mécanique&quot;</code> | 1 |
| <code>&quot;Handwerker&quot;</code> | 1 |
| <code>&quot;Hardware Engineering&quot;</code> | 1 |
| <code>&quot;Herbal&quot;</code> | 1 |
| <code>&quot;Hi Tech&quot;</code> | 1 |
| <code>&quot;Holding&quot;</code> | 1 |
| <code>&quot;Home &amp; Personal Care&quot;</code> | 1 |
| <code>&quot;Hospital&quot;</code> | 1 |
| <code>&quot;Hälso- &amp; sjukvård&quot;</code> | 1 |
| <code>&quot;Immigration&quot;</code> | 1 |
| <code>&quot;Immobilie&quot;</code> | 1 |
| <code>&quot;Immobilier et Biens&quot;</code> | 1 |
| <code>&quot;Imobiliária/gestão de propriedade&quot;</code> | 1 |
| <code>&quot;Impiego - Reclutamento - Assunzione personale&quot;</code> | 1 |
| <code>&quot;Impression / Emballage / Publication&quot;</code> | 1 |
| <code>&quot;Industrial / Services US Based&quot;</code> | 1 |
| <code>&quot;Industriale&quot;</code> | 1 |
| <code>&quot;Indústria&quot;</code> | 1 |
| <code>&quot;InfoSec&quot;</code> | 1 |
| <code>&quot;Information Technology &amp; Services&quot;</code> | 1 |
| <code>&quot;Information Technology Analysis &amp; Design&quot;</code> | 1 |
| <code>&quot;Ingegneria&quot;</code> | 1 |
| <code>&quot;Ingénierie écologique&quot;</code> | 1 |
| <code>&quot;Inmuebles&quot;</code> | 1 |
| <code>&quot;Inny&quot;</code> | 1 |
| <code>&quot;Inspection&quot;</code> | 1 |
| <code>&quot;Instalación&quot;</code> | 1 |
| <code>&quot;Insurance (Maritime)&quot;</code> | 1 |
| <code>&quot;Intrattenimento&quot;</code> | 1 |
| <code>&quot;Janitor&quot;</code> | 1 |
| <code>&quot;Keine&quot;</code> | 1 |
| <code>&quot;Kommunikationen&quot;</code> | 1 |
| <code>&quot;Konstruktion&quot;</code> | 1 |
| <code>&quot;Kosmetik&quot;</code> | 1 |
| <code>&quot;Laboratoire pharmaceutique&quot;</code> | 1 |
| <code>&quot;Learning Disabilities&quot;</code> | 1 |
| <code>&quot;Legal (Maritime)&quot;</code> | 1 |
| <code>&quot;Lehrkraft / Dozent&quot;</code> | 1 |
| <code>&quot;Library Science&quot;</code> | 1 |
| <code>&quot;Live Event and Production Services&quot;</code> | 1 |
| <code>&quot;Livsmedel&quot;</code> | 1 |
| <code>&quot;Logistique, Approvisionnement &amp; Transport&quot;</code> | 1 |
| <code>&quot;Logopädie&quot;</code> | 1 |
| <code>&quot;Läkemedel&quot;</code> | 1 |
| <code>&quot;Läkemedel &amp; Bioteknik&quot;</code> | 1 |
| <code>&quot;MX General Engineering&quot;</code> | 1 |
| <code>&quot;Machine Learning, AI &amp; Data Science&quot;</code> | 1 |
| <code>&quot;Maloprodaja i veleprodaja&quot;</code> | 1 |
| <code>&quot;Manufactura&quot;</code> | 1 |
| <code>&quot;Marketing Digital&quot;</code> | 1 |
| <code>&quot;Marketing Digital / Tecnología&quot;</code> | 1 |
| <code>&quot;Marknad&quot;</code> | 1 |
| <code>&quot;Matériel&quot;</code> | 1 |
| <code>&quot;Mecánica&quot;</code> | 1 |
| <code>&quot;Media and Entertainment&quot;</code> | 1 |
| <code>&quot;Medicina&quot;</code> | 1 |
| <code>&quot;Mental Health&quot;</code> | 1 |
| <code>&quot;Miljö&quot;</code> | 1 |
| <code>&quot;Mode&quot;</code> | 1 |
| <code>&quot;Médias, Rédaction Francophone&quot;</code> | 1 |
| <code>&quot;NBFC, Fintech&quot;</code> | 1 |
| <code>&quot;NGO sector&quot;</code> | 1 |
| <code>&quot;Nettoyage Industriel&quot;</code> | 1 |
| <code>&quot;Network Operations&quot;</code> | 1 |
| <code>&quot;ONG/Servicios sociales&quot;</code> | 1 |
| <code>&quot;Ocean Cruise&quot;</code> | 1 |
| <code>&quot;Office Management&quot;</code> | 1 |
| <code>&quot;Online Live Learning&quot;</code> | 1 |
| <code>&quot;Ontwerp&quot;</code> | 1 |
| <code>&quot;Operations &amp; Facilities&quot;</code> | 1 |
| <code>&quot;PARRUCCHIERE&quot;</code> | 1 |
| <code>&quot;Peer Recovery Coaching&quot;</code> | 1 |
| <code>&quot;Personal&quot;</code> | 1 |
| <code>&quot;Personal- und Haushaltsdienste&quot;</code> | 1 |
| <code>&quot;Personalvermittlung/Arbeitsvermittlung&quot;</code> | 1 |
| <code>&quot;Personnel administratif/Administrative Staff&quot;</code> | 1 |
| <code>&quot;Pharmacie&quot;</code> | 1 |
| <code>&quot;Physiotherapie&quot;</code> | 1 |
| <code>&quot;Pilotage&quot;</code> | 1 |
| <code>&quot;Podologie&quot;</code> | 1 |
| <code>&quot;Polymère / Plastique / Caoutchouc&quot;</code> | 1 |
| <code>&quot;Product &amp; Design&quot;</code> | 1 |
| <code>&quot;Product Development&quot;</code> | 1 |
| <code>&quot;Product Engineering&quot;</code> | 1 |
| <code>&quot;Product Footwear&quot;</code> | 1 |
| <code>&quot;Project Management &amp; Design&quot;</code> | 1 |
| <code>&quot;Projetos&quot;</code> | 1 |
| <code>&quot;Property&quot;</code> | 1 |
| <code>&quot;Psychology and Counseling&quot;</code> | 1 |
| <code>&quot;Public Safety&quot;</code> | 1 |
| <code>&quot;Publishing&quot;</code> | 1 |
| <code>&quot;Pénzügyi szolgáltatások&quot;</code> | 1 |
| <code>&quot;Quality Engineering (QE)&quot;</code> | 1 |
| <code>&quot;Računovodstvo&quot;</code> | 1 |
| <code>&quot;Real Estate &amp; Propiedades&quot;</code> | 1 |
| <code>&quot;Recrutement&quot;</code> | 1 |
| <code>&quot;Rekrytering&quot;</code> | 1 |
| <code>&quot;Reparation &amp; Underhåll&quot;</code> | 1 |
| <code>&quot;Retail Sales \\u2013 Apple&quot;</code> | 1 |
| <code>&quot;Retail Service&quot;</code> | 1 |
| <code>&quot;Ricerca e sviluppo&quot;</code> | 1 |
| <code>&quot;RnD&quot;</code> | 1 |
| <code>&quot;Récréologie&quot;</code> | 1 |
| <code>&quot;Résidence Seniors&quot;</code> | 1 |
| <code>&quot;SALES REGIONAL&quot;</code> | 1 |
| <code>&quot;SME Sales&quot;</code> | 1 |
| <code>&quot;Sanitaire-Chauffage-Plomberie&quot;</code> | 1 |
| <code>&quot;Science et technologie&quot;</code> | 1 |
| <code>&quot;Secteur public et gouvernement&quot;</code> | 1 |
| <code>&quot;Security Guard Services&quot;</code> | 1 |
| <code>&quot;Services de location&quot;</code> | 1 |
| <code>&quot;Services publics&quot;</code> | 1 |
| <code>&quot;Servicios de reparación/mantenimiento&quot;</code> | 1 |
| <code>&quot;Servicios financieros&quot;</code> | 1 |
| <code>&quot;Servizi sociali&quot;</code> | 1 |
| <code>&quot;Serviço ao cliente&quot;</code> | 1 |
| <code>&quot;Serviços pessoais e domésticos&quot;</code> | 1 |
| <code>&quot;Social Impact&quot;</code> | 1 |
| <code>&quot;Social Média&quot;</code> | 1 |
| <code>&quot;Software Engineering&quot;</code> | 1 |
| <code>&quot;Solar- EPC&quot;</code> | 1 |
| <code>&quot;Soldadura&quot;</code> | 1 |
| <code>&quot;Solutions consultancy&quot;</code> | 1 |
| <code>&quot;Sport, Freizeit und Lifestyle&quot;</code> | 1 |
| <code>&quot;Stretch Therapist&quot;</code> | 1 |
| <code>&quot;Stretch Therapist @ Google&quot;</code> | 1 |
| <code>&quot;Sécurité&quot;</code> | 1 |
| <code>&quot;Sécurité civile&quot;</code> | 1 |
| <code>&quot;Sécurité publique&quot;</code> | 1 |
| <code>&quot;Tabletop Games &amp; Hobby&quot;</code> | 1 |
| <code>&quot;Tasks/Projects&quot;</code> | 1 |
| <code>&quot;Technik&quot;</code> | 1 |
| <code>&quot;Technologie de l&#x27;information&quot;</code> | 1 |
| <code>&quot;Technologies de l&#x27;information&quot;</code> | 1 |
| <code>&quot;Tecnología / Desarrollo Web&quot;</code> | 1 |
| <code>&quot;Telecommunications;Internet&quot;</code> | 1 |
| <code>&quot;Telecomunicazioni&quot;</code> | 1 |
| <code>&quot;Telekom&quot;</code> | 1 |
| <code>&quot;Ticketing (Maritime)&quot;</code> | 1 |
| <code>&quot;Trading Operations&quot;</code> | 1 |
| <code>&quot;Tyres&quot;</code> | 1 |
| <code>&quot;Urology&quot;</code> | 1 |
| <code>&quot;VFX Supervisor&quot;</code> | 1 |
| <code>&quot;Valuation &amp; Biz-Modeling&quot;</code> | 1 |
| <code>&quot;Vario&quot;</code> | 1 |
| <code>&quot;Ventas&quot;</code> | 1 |
| <code>&quot;Ventes et Marketing&quot;</code> | 1 |
| <code>&quot;Verwaltung&quot;</code> | 1 |
| <code>&quot;Veterinary / Animal Health&quot;</code> | 1 |
| <code>&quot;Veterinary Support Staff&quot;</code> | 1 |
| <code>&quot;Voyage et tourisme&quot;</code> | 1 |
| <code>&quot;WTP Industry Preferred&quot;</code> | 1 |
| <code>&quot;Web Hosting and Data Center&quot;</code> | 1 |
| <code>&quot;Wireless&quot;</code> | 1 |
| <code>&quot;Zatrudnienie \\u2014 rekrutacja \\u2014 obsada stanowisk&quot;</code> | 1 |
| <code>&quot;Zoho&quot;</code> | 1 |
| <code>&quot;eCommerce&quot;</code> | 1 |
| <code>&quot;Área 2&quot;</code> | 1 |
| <code>&quot;Értékesítés \\u2013 marketing&quot;</code> | 1 |
| <code>&quot;أخرى&quot;</code> | 1 |
| <code>&quot;استيراد - تصدير&quot;</code> | 1 |
| <code>&quot;الإطارات&quot;</code> | 1 |
| <code>&quot;الاتصالات&quot;</code> | 1 |
| <code>&quot;التجارة والتسويق&quot;</code> | 1 |
| <code>&quot;التجارة والخدمات&quot;</code> | 1 |
| <code>&quot;الخدمات المالية&quot;</code> | 1 |
| <code>&quot;السيارات&quot;</code> | 1 |
| <code>&quot;الكمبيوتر&quot;</code> | 1 |
| <code>&quot;اللوجستيات&quot;</code> | 1 |
| <code>&quot;المحاسبة&quot;</code> | 1 |
| <code>&quot;بدون&quot;</code> | 1 |
| <code>&quot;كل الأقسام&quot;</code> | 1 |
| <code>&quot;通信業&quot;</code> | 1 |

</details>

## Fields unavailable in this snapshot

The schema has no job description, salary or currency, city/region/address, company name or company profile, skills list, occupation/industry code, seniority/experience requirement, education requirement, applicant count, headcount per posting, or hiring outcome. Company IDs alone cannot supply employer names, size, or industry. Titles and departments do not provide measured skill requirements. Application URLs are present, but their contents were not fetched and are not part of this inspection.

## Limits for job-market analysis

- This is a historical metadata snapshot, not a live inventory. `active` and `closed` are recorded source statuses; no posting URLs or current availability were verified.
- Coverage and sampling representativeness are not established by this file. The United States label accounts for **241,675 of 400,000 rows (60.41875%)**. Country counts describe this source, not national vacancy totals or relative labor demand.
- Missing departments, location labels, employment labels, and timestamps can bias grouped summaries. Missing values must remain visible rather than being assigned guessed categories.
- Category aliases and multilingual labels split otherwise potentially related groups. No country, employment, department, or occupational harmonization was performed here.
- Old and future posting dates, dates after fetch, and negative observed durations limit chronological analysis. Monthly counts are counts of source rows, not verified posting flows or hiring trends.
- Source IDs are unique here, but repeated real-world vacancies, repostings, and source coverage differences have not been resolved. Row counts are not measured numbers of hires, employers seeking staff, or positions available.
- The remote share describes a source boolean; it does not measure remote-work prevalence across the workforce or establish hybrid eligibility.
- Salary, skills demand, employer demographics, city-level demand, and time to hire cannot be measured from the available fields.
- The application defaults to the first 25,000 rows in sorted-file order, not a random sample. This document describes the full raw file; dashboard totals depend on pipeline limits, rejected records, and previously stored data.

## Reproducing the measurements

From the repository directory, install the pinned PyArrow dependency and run the following read-only Python code. It prints the schema, all null/blank counts, exact ID duplication statistics, every category value and frequency, date bounds, chronology checks, and before/after hashes. It does not run ingestion or write to the dataset.

```powershell
python -m pip install pyarrow==19.0.1
```

```python
from pathlib import Path
from hashlib import sha256
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

path = Path("data/part-0.parquet")
before = sha256(path.read_bytes()).hexdigest()
data = pq.read_table(path)
print("Rows:", data.num_rows, "metadata:", pq.ParquetFile(path).metadata.num_rows)
print(data.schema)
for field in data.schema:
    column = data[field.name]
    blanks = (pc.sum(pc.equal(pc.utf8_trim_whitespace(column), "")).as_py()
              if pa.types.is_string(field.type) else None)
    print(field.name, "null:", column.null_count, "blank:", blanks)
for key in ["id", "job_id"]:
    values = [r for r in pc.value_counts(data[key]).to_pylist()
              if r["values"] is not None]
    print(key, "distinct:", len(values),
          "repeated values:", sum(r["counts"] > 1 for r in values),
          "extra rows:", sum(r["counts"] - 1 for r in values))
for key in ["status", "workplace_type", "is_remote", "country",
            "employment_type", "department"]:
    values = sorted(pc.value_counts(data[key]).to_pylist(),
                    key=lambda r: (-r["counts"], str(r["values"])))
    assert sum(r["counts"] for r in values) == data.num_rows
    print(key, "distinct non-null:", pc.count_distinct(data[key]).as_py())
    for row in values:
        print(repr(row["values"]), row["counts"])
for key in ["posted_at", "fetched_time", "close_time"]:
    print(key, "non-null:", pc.count(data[key]).as_py(),
          "bounds:", pc.min_max(data[key]).as_py())
print("Paired posting/closing dates:", pc.sum(pc.and_(
    pc.is_valid(data["posted_at"]), pc.is_valid(data["close_time"]))).as_py())
print("Close before post:", pc.sum(pc.less(data["close_time"], data["posted_at"])).as_py())
print("Post after fetch:", pc.sum(pc.greater(data["posted_at"], data["fetched_time"])).as_py())
print("Remote disagreements:", pc.sum(pc.not_equal(
    data["is_remote"], pc.equal(data["workplace_type"], "remote"))).as_py())
after = sha256(path.read_bytes()).hexdigest()
assert before == after
print("SHA-256:", before, "unchanged:", before == after)
```
