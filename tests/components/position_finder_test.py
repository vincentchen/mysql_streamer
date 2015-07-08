# -*- coding: utf-8 -*-
import mock
import pytest

from replication_handler.components.position_finder import PositionFinder
from replication_handler.models.database import rbr_state_session
from replication_handler.models.global_event_state import EventType
from replication_handler.models.schema_event_state import SchemaEventState
from replication_handler.models.schema_event_state import SchemaEventStatus
from replication_handler.util.position import GtidPosition


class TestPositionFinder(object):

    @pytest.fixture
    def create_table_statement(self):
        return "CREATE TABLE STATEMENT"

    @pytest.fixture
    def alter_table_statement(self):
        return "ALTER TABLE STATEMENT"

    @pytest.fixture
    def position_dict(self):
        return {"gtid": "sid:12"}

    @pytest.fixture
    def completed_schema_event_state(self, create_table_statement, position_dict):
        return SchemaEventState(
            position=position_dict,
            status=SchemaEventStatus.COMPLETED,
            query=create_table_statement,
            table_name="Business",
            create_table_statement=create_table_statement,
        )

    @pytest.fixture
    def pending_schema_event_state(
        self, create_table_statement, alter_table_statement, position_dict
    ):
        return SchemaEventState(
            position=position_dict,
            status=SchemaEventStatus.PENDING,
            query=alter_table_statement,
            table_name="Business",
            create_table_statement=create_table_statement,
        )

    @pytest.fixture
    def schema_event_position(self):
        return GtidPosition(gtid="sid:12")

    @pytest.yield_fixture
    def patch_get_latest_schema_event_state(self):
        with mock.patch.object(
            SchemaEventState,
            'get_latest_schema_event_state'
        ) as mock_get_latest_schema_event_state:
            yield mock_get_latest_schema_event_state

    @pytest.yield_fixture
    def patch_session_connect_begin(self):
        with mock.patch.object(
            rbr_state_session,
            'connect_begin'
        ) as mock_session_connect_begin:
            mock_session_connect_begin.return_value.__enter__.return_value = mock.Mock()
            yield mock_session_connect_begin

    def test_get_position_to_resume_tailing_from_when_there_is_pending_state(
        self,
        schema_event_position,
        pending_schema_event_state,
    ):
        position_finder = PositionFinder(
            global_event_state=mock.Mock(),
            pending_schema_event=pending_schema_event_state
        )
        position = position_finder.get_position_to_resume_tailing_from()
        assert position.to_dict() == schema_event_position.to_dict()

    def test_get_position_to_resume_tailing_from_when_there_is_no_pending_state(
        self,
        schema_event_position,
        patch_get_latest_schema_event_state,
        completed_schema_event_state,
        patch_session_connect_begin,
        position_dict
    ):
        global_event_state = mock.Mock(
            event_type=EventType.SCHEMA_EVENT,
            position=position_dict,
        )
        position_finder = PositionFinder(
            global_event_state=global_event_state,
            pending_schema_event=None
        )
        patch_get_latest_schema_event_state.return_value = completed_schema_event_state
        position = position_finder.get_position_to_resume_tailing_from()
        assert position.to_dict() == schema_event_position.to_dict()