# saaga-api

The SAAGA project aims to create an automated pipeline for characterizing chemical mixtures of gas phase using experimental rotational spectroscopy with the help of machine learning and other computational tools. An important part is to have a database of rotational spectrum of a comprehensive list of known species, as well as a RESTful API to allow convenient and efficient access and queries to the database.

The database is already set up and hosted on Amazon RDS. The RESTful API allows CRUD operations of the database, in which admins can perform the full CRUD operations while other users can read and query the database.
The API is under development and the database is yet to be filled with data. The API is written using Python and Django with Docker. The setup of the API is done, and database model development is in progress right now.
