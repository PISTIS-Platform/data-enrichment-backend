# Data Enrichment backend
Data Enrichment in PISTIS is responsible for bringing semantic meaning to datasets by transforming raw datasets into SQL tables that has a standardized table schema. Datsets in the form of CSV, XML, TXT and JSON can be transformed into queryable SQL tables using this service. This service has a GUI using which a user can visualize a raw dataset and select appropriate table schema of the resulting dataset. Options for column names in the new table schema is coming from the integrated PISTIS Data Model. On the GUI of the data enrichment service, the user is allowed to view appropriate properties of the PISTIS Data Model and select a new property to be the column name.

## Table of Contents

***

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
4. [Maintainer](#maintainer) 
5. [License](#license)


## Prerequisites

***

*  [Docker](https://www.docker.com/) >= 20

Not mandatory, but useful tools:

 * Docker Desktop
 * Postman

 ## Installation

***

1. Build docker image

```
docker build -t data-enrichment-backend .

```

2. Run docker compose

```
docker-compose up

```

## Maintainer

***

[Sangeetha Reji](mailto:sangeetha.reji@fokus.fraunhofer.de)

## License

***

[Apache 2.0](http://www.apache.org/licenses/LICENSE-2.0)