import pytest
from fastcrud.crud.fast_crud import FastCRUD


@pytest.mark.asyncio
async def test_count_no_filters(async_session, test_model, test_data):
    for item in test_data:
        async_session.add(test_model(**item))
    await async_session.commit()

    crud = FastCRUD(test_model)
    count = await crud.count(async_session)

    assert count == len(test_data)


@pytest.mark.asyncio
async def test_count_with_filters(async_session, test_model, test_data):
    for item in test_data:
        async_session.add(test_model(**item))
    await async_session.commit()

    filter_criteria = test_data[0]
    crud = FastCRUD(test_model)
    count = await crud.count(async_session, **filter_criteria)

    assert count == 1


@pytest.mark.asyncio
async def test_count_no_matching_records(async_session, test_model):
    non_existent_filter = {"name": "NonExistentName"}
    crud = FastCRUD(test_model)
    count = await crud.count(async_session, **non_existent_filter)

    assert count == 0


@pytest.mark.asyncio
async def test_count_with_advanced_filters(async_session, test_model, test_data):
    for item in test_data:
        async_session.add(test_model(**item))
    await async_session.commit()

    crud = FastCRUD(test_model)

    count_gt = await crud.count(async_session, tier_id__gt=1)
    assert count_gt == len([item for item in test_data if item["tier_id"] > 1])

    count_lt = await crud.count(async_session, tier_id__lt=2)
    assert count_lt == len([item for item in test_data if item["tier_id"] < 2])

    count_ne = await crud.count(async_session, name__ne=test_data[0]["name"])
    assert count_ne == len(test_data) - 1


@pytest.mark.asyncio
async def test_update_multiple_records_allow_multiple(
    async_session, test_model, test_data
):
    for item in test_data:
        async_session.add(test_model(**item))
    await async_session.commit()

    crud = FastCRUD(test_model)

    await crud.update(
        async_session, {"name": "UpdatedName"}, allow_multiple=True, tier_id=1
    )
    updated_count = await crud.count(async_session, name="UpdatedName")
    expected_count = len([item for item in test_data if item["tier_id"] == 1])

    assert updated_count == expected_count


@pytest.mark.asyncio
async def test_soft_delete_custom_columns(async_session, test_model, test_data):
    crud = FastCRUD(
        test_model,
        is_deleted_column="custom_is_deleted",
        deleted_at_column="custom_deleted_at",
    )
    for item in test_data:
        async_session.add(test_model(**item))
    await async_session.commit()

    existing_record = await crud.get(async_session, id=test_data[0]["id"])
    assert existing_record is not None, "Record should exist before deletion"

    await crud.delete(async_session, id=test_data[0]["id"], allow_multiple=False)

    deleted_record = await crud.get(async_session, id=test_data[0]["id"])

    if deleted_record is None:
        assert True, "Record is considered 'deleted' and is not fetched by default"
    else:
        assert (
            deleted_record.get("custom_is_deleted") is True
        ), "Record should be marked as deleted"
        assert (
            "custom_deleted_at" in deleted_record
            and deleted_record["custom_deleted_at"] is not None
        ), "Deletion timestamp should be set"
