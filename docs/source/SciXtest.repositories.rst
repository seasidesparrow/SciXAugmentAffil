.. SciXTemplatePipeline documentation master file, created by
   sphinx-quickstart on Tue May  2 15:24:55 2023.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

The Template Test Environment
====================================

.. image:: https://github.com/adsabs/SciXTemplatePipeline/actions/workflows/python_actions.yml/badge.svg
   :target: https://github.com/adsabs/SciXTemplatePipeline/actions/workflows/python_actions.yml
   :alt: Python CI actions

.. image:: https://coveralls.io/repos/github/adsabs/SciXTemplatePipeline/badge.svg?branch=main
   :target: https://coveralls.io/github/adsabs/SciXTemplatePipeline?branch=main
   :alt: Coverage Status


.. _APItests:

The Template API Tests
---------------------------------

Running ``gRPC`` tests currently requires implementing a fake gRPC server. To save some pain in that regard, the ``tests/API/test_template_server.py`` file contains a full mock server that is instantiated when ``pytest`` is run and torn down when all the tests in ``TemplateServer`` have completed.

.. code-block:: python

    def setUp(self):
        """Instantiate a Template server and return a stub for use in tests"""
        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=1))
        self.logger = Logging(logging)

        """This block instantiates a schema registry that the gRPC client can access"""
        self.schema_client = MockSchemaRegistryClient()
        self.VALUE_SCHEMA_FILE = (
            "SciXTEMPLATE/tests/stubdata/AVRO_schemas/TEMPLATEInputSchema.avsc"
        )
        self.VALUE_SCHEMA_NAME = "TEMPLATEInputSchema"
        self.value_schema = open(self.VALUE_SCHEMA_FILE).read()
        self.schema_client.register(self.VALUE_SCHEMA_NAME, Schema(self.value_schema, "AVRO"))
        self.schema = get_schema(self.logger, self.schema_client, self.VALUE_SCHEMA_NAME)
        self.avroserialhelper = AvroSerialHelper(self.schema, self.logger.logger)
        OUTPUT_VALUE_SCHEMA_FILE = (
            "SciXTEMPLATE/tests/stubdata/AVRO_schemas/TEMPLATEOutputSchema.avsc"
        )
        OUTPUT_VALUE_SCHEMA_NAME = "TEMPLATEOutputSchema"
        output_value_schema = open(OUTPUT_VALUE_SCHEMA_FILE).read()
        self.schema_client.register(OUTPUT_VALUE_SCHEMA_NAME, Schema(output_value_schema, "AVRO"))

        """The producer must be given an empty mock registry to function properly."""
        self.producer = AvroProducer({}, schema_registry=MockSchemaRegistryClient())


        """These lines add the individual servicers to the test server. They are identical to the calls in API/template_server.py""""
        template_grpc.add_TemplateInitServicer_to_server(
            Template(self.producer, self.schema, self.schema_client, self.logger.logger),
            self.server,
            self.avroserialhelper,
        )
        template_grpc.add_TemplateMonitorServicer_to_server(
            Template(self.producer, self.schema, self.schema_client, self.logger.logger),
            self.server,
            self.avroserialhelper,
        )

        """Sets the server port and starts the server"""
        self.port = 55551
        self.server.add_insecure_port(f"[::]:{self.port}")
        self.server.start()
