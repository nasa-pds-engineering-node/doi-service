import six
from connexion.apps.flask_app import FlaskJSONEncoder  # type: ignore
from pds_doi_service.api.models import Model


class JSONEncoder(FlaskJSONEncoder):
    """
    This encodes into JSON.
    """
    include_nulls = False

    def default(self, o):
        if isinstance(o, Model):
            dikt = {}
            for attr, _ in six.iteritems(o.swagger_types):
                value = getattr(o, attr)
                if value is None and not self.include_nulls:
                    continue
                attr = o.attribute_map[attr]
                dikt[attr] = value
            return dikt
        return FlaskJSONEncoder.default(self, o)
