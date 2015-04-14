#!/usr/bin/python

import cjson

d = cjson.decode(file("fnal.json").read())
o = d["phedex"]
o["proto"] = { "block": ["bytes", "files", "is_open", "name", "id",
                         {"replica": ["bytes", "files", "node", "time_create",
                                      "time_update", "group", "node_id",
                                      "custodial", "se", "subscribed",
                                      "complete"]} ]}
outblocks = []
inblocks = o["block"]
o["block"] = []
f = file("fnal-x.sjson", "w")
preamble = cjson.encode(o)
f.write(preamble[:-2] + "\n")
comma = " "

for ib in inblocks:
  ob = [int(ib["bytes"]), int(ib["files"]), ib["is_open"], ib["name"], int(ib["id"]), []]
  for r in ib["replica"]:
    ob[-1].append([int(r["bytes"]), int(r["files"]), r["node"],
                   float(r["time_create"]), float(r["time_update"]),
                   r["group"], int(r["node_id"]), r["custodial"],
                   r["se"], r["subscribed"], r["complete"]])
  f.write(comma + cjson.encode(ob) + "\n")
  comma = ","

f.write(preamble[-2:])
