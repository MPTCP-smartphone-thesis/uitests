package utils;

import java.io.DataOutputStream;
import java.util.ArrayList;
import java.util.List;

import com.android.uiautomator.core.UiCollection;
import com.android.uiautomator.core.UiObject;
import com.android.uiautomator.core.UiObjectNotFoundException;
import com.android.uiautomator.core.UiScrollable;
import com.android.uiautomator.core.UiSelector;
import com.android.uiautomator.testrunner.UiAutomatorTestCase;

public class Utils {

	public static void runAsRoot(String[] cmds) {
		try {
			Process p = Runtime.getRuntime().exec("su");
			DataOutputStream os = new DataOutputStream(p.getOutputStream());
			for (String tmpCmd : cmds) {
				os.writeBytes(tmpCmd + "\n");
			}
			os.writeBytes("exit\n");
			os.flush();
		} catch (Exception e) {
			e.getStackTrace();
		}
	}

	public static boolean openApp(UiAutomatorTestCase t, String appText,
			String packageName) throws UiObjectNotFoundException {
		t.getUiDevice().pressHome();

		UiObject allAppsButton = new UiObject(
				new UiSelector().description("Apps"));

		allAppsButton.clickAndWaitForNewWindow();

		UiScrollable appViews = new UiScrollable(
				new UiSelector().scrollable(true));

		appViews.setAsHorizontalList();

		UiObject settingsApp = appViews.getChildByText(new UiSelector()
				.className(android.widget.TextView.class.getName()), appText);

		settingsApp.clickAndWaitForNewWindow();

		// Validate that the package name is the expected one
		UiObject appValidation = new UiObject(
				new UiSelector().packageName(packageName));

		return appValidation.exists();
	}

	public static UiObject getObject(String id)
			throws UiObjectNotFoundException {
		UiObject obj = new UiObject(new UiSelector().resourceId(id));
		if (!obj.exists())
			throw new UiObjectNotFoundException("Object with id " + id
					+ " not found");
		return obj;
	}

	public static boolean hasObject(String id) {
		try {
			return getObject(id) != null;
		} catch (UiObjectNotFoundException e) {
			return false;
		}
	}

	public static boolean click(String id) {
		try {
			return click(getObject(id));
		} catch (UiObjectNotFoundException e) {
			return false;
		}
	}

	public static boolean click(UiObject obj) {
		try {
			return obj.click();
		} catch (UiObjectNotFoundException e) {
			return false;
		}
	}

	public static boolean clickAndWaitForNewWindow(String id) {
		try {
			return click(getObject(id));
		} catch (UiObjectNotFoundException e) {
			return false;
		}
	}

	public static boolean clickAndWaitForNewWindow(UiObject obj) {
		try {
			return obj.clickAndWaitForNewWindow();
		} catch (UiObjectNotFoundException e) {
			return false;
		}
	}

	public static boolean setText(String id, String text) {
		try {
			return setText(getObject(id), text);
		} catch (UiObjectNotFoundException e) {
			return false;
		}
	}

	public static boolean setText(UiObject obj, String text) {
		try {
			obj.clearTextField();
			return obj.setText(text);
		} catch (UiObjectNotFoundException e) {
			return false;
		}
	}

	public static boolean hasText(String id, String text) {
		try {
			return hasText(getObject(id), text);
		} catch (UiObjectNotFoundException e) {
			return false;
		}
	}

	public static boolean hasText(UiObject obj, String text) {
		try {
			return obj.getText().equals(text);
		} catch (UiObjectNotFoundException e) {
			return false;
		}
	}

	public static boolean hasTextAndClick(String id, String text) {
		if (hasText(id, text))
			return click(id);
		return true;
	}

	public static boolean hasTextAndClick(UiObject obj, String text) {
		if (hasText(obj, text))
			return click(obj);
		return true;
	}

	public static boolean scrollBackward(UiScrollable obj) {
		try {
			return obj.scrollBackward();
		} catch (UiObjectNotFoundException e) {
			return false;
		}
	}

	public static boolean scrollForward(UiScrollable obj) {
		try {
			return obj.scrollForward();
		} catch (UiObjectNotFoundException e) {
			return false;
		}
	}

	public static List<UiObject> getElems(String parentId, String childId) {
		List<UiObject> childs = new ArrayList<UiObject>();

		try {
			UiCollection parent = new UiCollection(
					new UiSelector().resourceId(parentId));
			int count = parent.getChildCount(new UiSelector()
					.resourceId(childId));

			for (int i = 0; i < count; ++i) {
				UiObject child = parent.getChild(new UiSelector().resourceId(
						childId).instance(i));
				childs.add(child);
			}
		} catch (UiObjectNotFoundException e) {
			e.printStackTrace();
		}

		return childs;
	}
}