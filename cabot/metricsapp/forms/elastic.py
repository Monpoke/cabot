from django.core.exceptions import ValidationError
from django.forms import ModelForm
from elasticsearch.client import ClusterClient
from elasticsearch.exceptions import ConnectionError
import json
from cabot.metricsapp.api import create_es_client, validate_query
from cabot.metricsapp.models import ElasticsearchSource, ElasticsearchStatusCheck


class ElasticsearchSourceForm(ModelForm):
    class Meta:
        model = ElasticsearchSource

    def clean_urls(self):
        """Make sure the input urls are valid Elasticsearch hosts."""
        input_urls = self.cleaned_data['urls']

        # Create an Elasticsearch test client and see if a health check for the instance succeeds
        try:
            client = create_es_client(input_urls)
            ClusterClient(client).health()
            return input_urls
        except ConnectionError:
            raise ValidationError('Invalid Elasticsearch host url(s).')


class ElasticsearchStatusCheckForm(ModelForm):
    class Meta:
        model = ElasticsearchStatusCheck
        fields = (
            'name',
            'source',
            'queries',
            'check_type',
            'warning_value',
            'high_alert_importance',
            'high_alert_value',
            'time_range',
            'frequency',
            'active',
            'retries',
        )

    def clean_queries(self):
        """
        Make sure input queries are formatted correctly.
        """
        queries = self.cleaned_data['queries']
        try:
            query_list = json.loads(queries)
        except ValueError:
            raise ValidationError('Queries must be json-parsable')

        for query in query_list:
            try:
                validate_query(query)
            except ValueError as e:
                raise ValidationError(e)

        return queries
