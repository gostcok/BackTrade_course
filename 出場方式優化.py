
import os
import polars as pl
import pandas as pd

dirname = r'C:\SysJust\XQLite\XS\Print'
os.chdir(dirname)

files=os.listdir(dirname)
rows=[]
for file in files:
    code=file.split("_")[1].split('.')[0]
    with open(file) as f:
        row={"code": code}
        contents = f.read().strip().split()
        # print(contents)
        if code=="6781":
            print(contents)
            for key,value in (content.split(":") for content in contents):
                if key not in row:
                    row[key]=[]
                row[key].append(value)
            rows.append(row)
df=pl.DataFrame(rows)
print(df.to_pandas().to_string())
mean_return = df.select(
    pl.col("報酬率")
      .str.replace("%", "")
      .cast(pl.Float64)
      .mean()
)

after_n_mean_return=[df.select(
                        pl.col(f"後{n}天報酬率")
                        .str.replace("%", "")
                        .cast(pl.Float64)
                        .mean()
                    ) for n in range(1,10)]
after_n_mean_return.append(df.select(
    pl.col("後N日報酬率")
      .str.replace("%", "")
      .cast(pl.Float64)
      .mean()
))

allreturn=[mean_return]+after_n_mean_return

# print(f'出場當下報酬率:{mean_return:2f}%,出場後10日:{afterN_mean_return:2f}%')
print(pl.concat(allreturn,how="horizontal"))
# print(afterN_mean_return)

# dup_codes = (
#     df.group_by("code")
#       .agg(pl.col("進場時間").n_unique().alias("count"))
#       .filter(pl.col("count") > 1)
#       .select("code")
# )

# result = df.join(dup_codes, on="code", how="inner")
# print(result)

