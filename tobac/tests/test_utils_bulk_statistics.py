from datetime import datetime
import numpy as np
import pandas as pd
import xarray as xr
import tobac
import tobac.utils as tb_utils
import tobac.testing as tb_test


def test_bulk_statistics():
    """
    Test to assure that bulk statistics for identified features are computed as expected.

    """

    ### Test 2D data with time dimension
    test_data = tb_test.make_simple_sample_data_2D().core_data()
    common_dset_opts = {
        "in_arr": test_data,
        "data_type": "iris",
    }
    test_data_iris = tb_test.make_dataset_from_arr(
        time_dim_num=0, y_dim_num=1, x_dim_num=2, **common_dset_opts
    )

    # detect features
    threshold = 7
    # test_data_iris = testing.make_dataset_from_arr(test_data, data_type="iris")
    fd_output = tobac.feature_detection.feature_detection_multithreshold(
        test_data_iris,
        dxy=1000,
        threshold=[threshold],
        n_min_threshold=100,
        target="maximum",
    )

    # perform segmentation with bulk statistics
    stats = {
        "segment_max": np.max,
        "segment_min": min,
        "percentiles": (np.percentile, {"q": 95}),
    }
    out_seg_mask, out_df = tobac.segmentation.segmentation_2D(
        fd_output, test_data_iris, dxy=1000, threshold=threshold, statistic=stats
    )

    #### checks

    #  assure that bulk statistics in postprocessing give same result
    out_segmentation = tb_utils.get_statistics_from_mask(
        out_df, out_seg_mask, test_data_iris, statistic=stats
    )
    assert out_segmentation.equals(out_df)

    # assure that column names in new dataframe correspond to keys in statistics dictionary
    for key in stats.keys():
        assert key in out_df.columns

    # assure that statistics bring expected result
    for frame in out_df.frame.values:
        assert out_df[out_df.frame == frame].segment_max.values[0] == np.max(
            test_data[frame]
        )

    ### Test the same with 3D data
    test_data_iris = tb_test.make_sample_data_3D_3blobs()

    # detect features in test dataset
    fd_output = tobac.feature_detection.feature_detection_multithreshold(
        test_data_iris,
        dxy=1000,
        threshold=[threshold],
        n_min_threshold=100,
        target="maximum",
    )

    # perform segmentation with bulk statistics
    stats = {
        "segment_max": np.max,
        "segment_min": min,
        "percentiles": (np.percentile, {"q": 95}),
    }
    out_seg_mask, out_df = tobac.segmentation.segmentation_3D(
        fd_output, test_data_iris, dxy=1000, threshold=threshold, statistic=stats
    )

    ##### checks #####

    #  assure that bulk statistics in postprocessing give same result
    out_segmentation = tb_utils.get_statistics_from_mask(
        out_df, out_seg_mask, test_data_iris, statistic=stats
    )
    assert out_segmentation.equals(out_df)

    # assure that column names in new dataframe correspond to keys in statistics dictionary
    for key in stats.keys():
        assert key in out_df.columns

    # assure that statistics bring expected result
    for frame in out_df.frame.values:
        assert out_df[out_df.frame == frame].segment_max.values[0] == np.max(
            test_data_iris.data[frame]
        )


def test_bulk_statistics_multiple_fields():
    """
    Test that multiple field input to bulk_statistics works as intended
    """

    test_labels = np.array(
        [
            [
                [0, 0, 0, 0, 0],
                [0, 1, 0, 2, 0],
                [0, 1, 0, 2, 0],
                [0, 1, 0, 0, 0],
                [0, 0, 0, 0, 0],
            ],
            [
                [0, 0, 0, 0, 0],
                [0, 3, 0, 0, 0],
                [0, 3, 0, 4, 0],
                [0, 3, 0, 4, 0],
                [0, 0, 0, 0, 0],
            ],
        ],
        dtype=int,
    )

    test_labels = xr.DataArray(
        test_labels,
        dims=("time", "y", "x"),
        coords={
            "time": [datetime(2000, 1, 1), datetime(2000, 1, 1, 0, 5)],
            "y": np.arange(5),
            "x": np.arange(5),
        },
    )

    test_values = np.array(
        [
            [
                [0, 0, 0, 0, 0],
                [0, 1, 0, 2, 0],
                [0, 2, 0, 2, 0],
                [0, 3, 0, 0, 0],
                [0, 0, 0, 0, 0],
            ],
            [
                [0, 0, 0, 0, 0],
                [0, 2, 0, 0, 0],
                [0, 3, 0, 3, 0],
                [0, 4, 0, 2, 0],
                [0, 0, 0, 0, 0],
            ],
        ]
    )

    test_values = xr.DataArray(
        test_values, dims=test_labels.dims, coords=test_labels.coords
    )

    test_weights = np.array(
        [
            [
                [0, 0, 0, 0, 0],
                [0, 0, 0, 1, 0],
                [0, 0, 0, 1, 0],
                [0, 1, 0, 0, 0],
                [0, 0, 0, 0, 0],
            ],
            [
                [0, 0, 0, 0, 0],
                [0, 1, 0, 0, 0],
                [0, 0, 0, 1, 0],
                [0, 0, 0, 1, 0],
                [0, 0, 0, 0, 0],
            ],
        ]
    )

    test_weights = xr.DataArray(
        test_weights, dims=test_labels.dims, coords=test_labels.coords
    )

    test_features = pd.DataFrame(
        {
            "feature": [1, 2, 3, 4],
            "frame": [0, 0, 1, 1],
            "time": [
                datetime(2000, 1, 1),
                datetime(2000, 1, 1),
                datetime(2000, 1, 1, 0, 5),
                datetime(2000, 1, 1, 0, 5),
            ],
        }
    )

    statistics_mean = {"mean": np.mean}

    expected_mean_result = np.array([2, 2, 3, 2.5])

    bulk_statistics_output = tb_utils.get_statistics_from_mask(
        test_features, test_labels, test_values, statistic=statistics_mean
    )

    statistics_weighted_mean = {
        "weighted_mean": (lambda x, y: np.average(x, weights=y))
    }

    expected_weighted_mean_result = np.array([3, 2, 2, 2.5])

    bulk_statistics_output = tb_utils.get_statistics_from_mask(
        bulk_statistics_output,
        test_labels,
        test_values,
        test_weights,
        statistic=statistics_weighted_mean,
    )

    assert np.all(bulk_statistics_output["mean"] == expected_mean_result)
    assert np.all(
        bulk_statistics_output["weighted_mean"] == expected_weighted_mean_result
    )


def test_bulk_statistics_time_invariant_field():
    """
    Some fields, such as area, are time invariant, and so passing an array with
    a time dimension is memory inefficient. Here we test if
    `get_statistics_from_mask` works if an input field has no time dimension,
    by passing the whole field to `get_statistics` rather than a time slice.
    """

    test_labels = np.array(
        [
            [
                [0, 0, 0, 0, 0],
                [0, 1, 0, 2, 0],
                [0, 1, 0, 2, 0],
                [0, 1, 0, 0, 0],
                [0, 0, 0, 0, 0],
            ],
            [
                [0, 0, 0, 0, 0],
                [0, 3, 0, 0, 0],
                [0, 3, 0, 4, 0],
                [0, 3, 0, 4, 0],
                [0, 0, 0, 0, 0],
            ],
        ],
        dtype=int,
    )

    test_labels = xr.DataArray(
        test_labels,
        dims=("time", "y", "x"),
        coords={
            "time": [datetime(2000, 1, 1), datetime(2000, 1, 1, 0, 5)],
            "y": np.arange(5),
            "x": np.arange(5),
        },
    )

    test_areas = np.array(
        [
            [0.25, 0.5, 0.75, 1, 1],
            [0.25, 0.5, 0.75, 1, 1],
            [0.25, 0.5, 0.75, 1, 1],
            [0.25, 0.5, 0.75, 1, 1],
            [0.25, 0.5, 0.75, 1, 1],
        ]
    )

    test_areas = xr.DataArray(
        test_areas,
        dims=("y", "x"),
        coords={
            "y": np.arange(5),
            "x": np.arange(5),
        },
    )

    test_features = pd.DataFrame(
        {
            "feature": [1, 2, 3, 4],
            "frame": [0, 0, 1, 1],
            "time": [
                datetime(2000, 1, 1),
                datetime(2000, 1, 1),
                datetime(2000, 1, 1, 0, 5),
                datetime(2000, 1, 1, 0, 5),
            ],
        }
    )

    statistics_sum = {"sum": np.sum}

    expected_sum_result = np.array([1.5, 2, 1.5, 2])

    bulk_statistics_output = tb_utils.get_statistics_from_mask(
        test_features, test_labels, test_areas, statistic=statistics_sum
    )

    assert np.all(bulk_statistics_output["sum"] == expected_sum_result)


def test_bulk_statistics_broadcasting():
    """
    Test whether field broadcasting works for bulk_statistics, with both leading and trailing dimensions tested
    """
    test_labels = np.array(
        [
            [
                [0, 0, 0, 0, 0],
                [0, 1, 0, 2, 0],
                [0, 1, 0, 2, 0],
                [0, 1, 0, 0, 0],
                [0, 0, 0, 0, 0],
            ],
            [
                [0, 0, 0, 0, 0],
                [0, 3, 0, 0, 0],
                [0, 3, 0, 4, 0],
                [0, 3, 0, 4, 0],
                [0, 0, 0, 0, 0],
            ],
        ],
        dtype=int,
    )

    test_labels = xr.DataArray(
        test_labels,
        dims=("time", "y", "x"),
        coords={
            "time": [datetime(2000, 1, 1), datetime(2000, 1, 1, 0, 5)],
            "y": np.arange(5),
            "x": np.arange(5),
        },
    )

    test_values = np.array(
        [
            [0.25, 0.5, 0.75, 1, 1],
            [1.25, 1.5, 1.75, 2, 2],
        ]
    )

    test_values = xr.DataArray(
        test_values,
        dims=("time", "x"),
        coords={"time": test_labels.time, "x": test_labels.x},
    )

    test_weights = np.array([0, 0, 1, 0, 0]).reshape([5, 1])

    test_weights = xr.DataArray(
        test_weights, dims=("y", "z"), coords={"y": test_labels.y}
    )

    test_features = pd.DataFrame(
        {
            "feature": [1, 2, 3, 4],
            "frame": [0, 0, 1, 1],
            "time": [
                datetime(2000, 1, 1),
                datetime(2000, 1, 1),
                datetime(2000, 1, 1, 0, 5),
                datetime(2000, 1, 1, 0, 5),
            ],
        }
    )

    statistics_sum = {"sum": np.sum}

    expected_sum_result = np.array([1.5, 2, 4.5, 4])

    bulk_statistics_output = tb_utils.get_statistics_from_mask(
        test_features, test_labels, test_values, statistic=statistics_sum
    )

    statistics_weighted_sum = {"weighted_sum": (lambda x, y: np.sum(x * y))}

    expected_weighted_sum_result = np.array([0.5, 1, 1.5, 2])

    bulk_statistics_output = tb_utils.get_statistics_from_mask(
        bulk_statistics_output,
        test_labels,
        test_values,
        test_weights,
        statistic=statistics_weighted_sum,
    )

    assert np.all(bulk_statistics_output["sum"] == expected_sum_result)
    assert np.all(
        bulk_statistics_output["weighted_sum"] == expected_weighted_sum_result
    )
