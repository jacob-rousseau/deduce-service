import io
import json

import deduce_app
import examples
import pytest
from deduce_app import app


@pytest.fixture
def client():
    deduce_app.initialize_deduce()
    with app.test_client() as client:
        yield client


class TestDeduceService:
    def test_deidentify_none(self, client):

        example_data = {"text": None, "id": "8345"}

        response = client.post(
            "/deidentify",
            data=json.dumps(example_data),
            headers={"Content-Type": "application/json"},
        )
        data = response.get_json()

        assert data["text"] is None

    def test_deidentify_id(self, client):

        example_data = {"text": None, "id": "8345"}

        response = client.post(
            "/deidentify",
            data=json.dumps(example_data),
            headers={"Content-Type": "application/json"},
        )
        data = response.get_json()

        assert data["id"] == example_data["id"]

    def test_deidentify(self, client):

        example_data = examples.example_text

        response = client.post(
            "/deidentify",
            data=json.dumps(example_data),
            headers={"Content-Type": "application/json"},
        )
        data = response.get_json()

        # Test whether the patient name is removed
        assert "Jansen" not in data["text"]
        # Test whether the patient name has been replaced
        assert "[PATIENT]" in data["text"]
        # Test whether other functional parts are still included
        assert "ontslagen van de kliniek" in data["text"]

    def test_deidentify_date_default(self, client):
        """
        Test that dates get deidentified when no dates argument is set.
        """

        input_data = {"text": "20 maart 2021"}

        response = client.post(
            "/deidentify",
            data=json.dumps(input_data),
            headers={"Content-Type": "application/json"},
        )
        output_data = response.get_json()

        assert output_data["text"] == "[DATUM-1]"

    def test_deidentify_date_true(self, client):
        """
        Test that dates get deidentified when dates argument is set to true.
        """

        input_data = {"text": "20 maart 2021", "disabled": []}

        response = client.post(
            "/deidentify",
            data=json.dumps(input_data),
            headers={"Content-Type": "application/json"},
        )
        output_data = response.get_json()

        assert output_data["text"] == "[DATUM-1]"

    def test_deidentify_without_dates(self, client):
        """
        Test that dates do not get deidentified when dates argument is set to false.
        """

        input_data = {"text": "20 maart 2021", "disabled": ["dates"]}

        response = client.post(
            "/deidentify",
            data=json.dumps(input_data),
            headers={"Content-Type": "application/json"},
        )
        output_data = response.get_json()

        assert output_data["text"] == input_data["text"]

    def test_deidentify_bulk(self, client):

        example_data_bulk = examples.example_texts

        response = client.post(
            "/deidentify_bulk",
            data=json.dumps(example_data_bulk),
            headers={"Content-Type": "application/json"},
        )
        data = response.get_json()

        assert len(data["texts"]) == 2
        assert "Jong" not in data["texts"][1]["text"]
        assert "jong" in data["texts"][1]["text"]

    def test_deidentify_bulk_disabled(self, client):

        example_data_bulk = examples.example_texts
        example_data_bulk["disabled"] = ["names"]

        response = client.post(
            "/deidentify_bulk",
            data=json.dumps(example_data_bulk),
            headers={"Content-Type": "application/json"},
        )
        data = response.get_json()

        assert len(data["texts"]) == 2
        assert "Jan Jansen" in data["texts"][0]["text"]
        assert "Jong" in data["texts"][1]["text"]
        assert "jong" in data["texts"][1]["text"]

    def test_convert_line(self, client):

        to_test = "HASH_A\tNOTE_ID_1234\tNOTE_CAT_NURSING_NOTITION\tPeter\tP.\tRabbit\tRABBIT,P.\tRabbit-Konijn\t" \
                  "Peter was not very well during the evening. His mother put him to bed, and made some chamomile " \
                  "tea: One table-spoonful to be taken at bedtime"
        values = to_test.strip().split('\t')
        data = deduce_app.convert_line(values)
        assert data["hash_id"] == "HASH_A"
        assert data["note_id"] == "NOTE_ID_1234"
        assert data["note_cat"] == "NOTE_CAT_NURSING_NOTITION"
        assert data["patient_first_names"] == "Peter"
        assert data["patient_initials"] == "P."
        assert data["patient_surname"] == "Rabbit"
        assert data["patient_surname_capitals"] == "RABBIT,P."
        assert data["patient_surname_2"] == "Rabbit-Konijn"
        assert data["text"] == "Peter was not very well during the evening. His mother put him to bed, and made " \
                               "some chamomile tea: One table-spoonful to be taken at bedtime"

    def test_deindentification_extra_fields(self, client):
        to_test = "HASH_B\tNOTE_ID_0002\tNOTE_CAT_LETTER\tPeter John\tP.J.\tRabbit\tRABBIT,P.\tRabbit-Konijn\t" \
                  "The patient P. Rabbit (first name Peter) was admitted to our hospital " \
                  "on 14-02-2023 with symptoms of chamomile tea poisoning. His mother " \
                  "Mrs. Rabbit-Konijn, admitted administrating too much tea. His initials are P.J. and his given" \
                  "names are Peter John. Patient name: RABBIT,P. His compound uppercase name is RABBIT,P!"
        expected = "[PATIENT] (first name [PATIENT]) was admitted to our hospital " \
                   "on [DATUM-1] with symptoms of chamomile tea poisoning. His mother " \
                   "[PATIENT], admitted administrating too much tea. His initials are [PATIENT]. and his given" \
                   "names are [PATIENT]. Patient name: [PATIENT]. His compound uppercase name is [PATIENT]!"
        values = to_test.strip().split('\t')
        data = deduce_app.convert_line(values)
        deidentified = deduce_app.annotate_text(data)
        assert deidentified["text"] == expected

    def test_capitalized_surname(self, client):
        # use a surname present in the lookup-list with surnames in the clinical text while in the surname it's in
        # lower-case
        to_test = "123456789ABCDEF\t1234\tBrief\tPietje Firstname2 Firstname3\tI.N.I.T.I.A.L.S.\tHartsuiker\t" \
                  "FAMILYNAME.I.N.I.T.I.A.L.S.\tPietje\tDe heer HARTSUIKER was admitted to our hospital on " \
                  "01-06-2022 with appendicitis."
        expected = "De heer [PATIENT] was admitted to our hospital on [DATUM-1] with appendicitis."
        values = to_test.strip().split('\t')
        data = deduce_app.convert_line(values)
        deidentified = deduce_app.annotate_text(data)
        assert deidentified["text"] == expected

    def test_deidentify_tab_delimited_file(self, client):
        file_name = "./data/input_from_file.tsv"
        output = io.StringIO()
        deduce_app.deidentify_tab_delimited_file(file_name, output)
        result = output.getvalue()
        output.close()
        assert True == ("[PATIENT] was not very well during the evening, [DATUM-1]." in result)
