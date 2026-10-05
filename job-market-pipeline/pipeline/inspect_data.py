from pathlib import Path
from collections import Counter
import pyarrow.parquet as pq
root=Path(__file__).resolve().parents[1]
for path in sorted((root/'data').glob('*.parquet')):
 file=pq.ParquetFile(path)
 print(path.name, 'rows:',file.metadata.num_rows, 'schema:',file.schema_arrow)
 missing=Counter(); categories={k:Counter() for k in ['country','status','employment_type','workplace_type']};seen=set();duplicates=0
 for batch in file.iter_batches(batch_size=5000):
  for row in batch.to_pylist():
   missing.update(k for k,v in row.items() if v is None)
   for k,counts in categories.items():counts[row.get(k)]+=1
   duplicates+=row['id'] in seen;seen.add(row['id'])
 print('Missing:',dict(missing));print('Duplicate ids:',duplicates)
 for key,counts in categories.items():print(key,counts.most_common(20))
