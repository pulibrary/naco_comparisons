# Authorities Comparison

Creaky little scripts to compare our local authorities to LC. May be refined as part of our data quality efforts. 
* `get_uris_from_dump.py` for names and subjects on the same machine as the triplestore (Fuseki)
* `compare_vger_lc.py -[sn][v][r]`
 * files of lccns are output to `./out`
 * produces venn diagrams (see below: subjects on the left, names on the right)

![subjects](https://raw.githubusercontent.com/pulibrary/naco_comparisons/master/images/sub_venn.png)
![names](https://raw.githubusercontent.com/pulibrary/naco_comparisons/master/images/names_venn_201904.png)

## Voyager vs. id.loc(+Ward) 2019
The basic process ...

### Voyager
Get lccns from Voyager

`SELECT AUTH_ID,princetondb.GetAuthSubfield(AUTH_MASTER.AUTH_ID,'010','a') as field010a 
FROM AUTH_MASTER`

### LC (id.loc dumps)
#### get latest change dates
* names: posted 26 Dec 2018 (last change `2018-12-12T22:38:06`)
  * last change: `SELECT (max(?change) as ?changedate) WHERE { ?s <http://id.loc.gov/ontologiesRecordInfo#recordChangeDate> ?change . }`
* subjects: posted 9 Nov 2018 (last change `2018-11-01T14:38:55`)
  * last change: `SELECT (max(?change) as ?changedate) WHERE { ?s <http://www.loc.gov/mads/rdf/v1#adminMetadata> ?bn . ?bn <http://id.loc.gov/ontologies/RecordInfo#recordChangeDate> ?change . }`

#### get lccns from dumps
`SELECT ?s WHERE {
  ?s <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.loc.gov/mads/rdf/v1#Authority> .
  FILTER NOT EXISTS { ?s <http://www.loc.gov/mads/rdf/v1#useInstead> ?o } .
  FILTER NOT EXISTS { ?s <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.loc.gov/mads/rdf/v1#Variant> } .
  FILTER NOT EXISTS { ?s <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.loc.gov/mads/rdf/v1#DeprecatedAuthority> } .
}`

### Ward files
Loop over Ward files 2018 - 2019 (based on latest change dates of dumps) and eliminate any with LDR/05 other than `c` or `n`

### Combine Ward + id.loc ids
Create sets and combine them

### Compare Voyager lccns vs. id.loc + Ward
... by creating sets and finding the difference
