package utils;

import java.io.DataOutputStream;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;

import android.os.RemoteException;

import com.android.uiautomator.core.UiCollection;
import com.android.uiautomator.core.UiObject;
import com.android.uiautomator.core.UiObjectNotFoundException;
import com.android.uiautomator.core.UiScrollable;
import com.android.uiautomator.core.UiSelector;
import com.android.uiautomator.testrunner.UiAutomatorTestCase;

public class Utils {
	public enum Orientation {
		LEFT, RIGHT, UP, DOWN
	};

	public static final String homeDir = "/storage/sdcard0";
	public static final String traceBase = homeDir + "/traces";

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

	/**
	 * Create a new file in /storage/sdcard0
	 * @pre: /storage/sdcard0/random_seed_orig should be present and we need
	 *       root rights (easier for us)
	 * @param output: name of the output file
	 */
	public static void createFile(String output) {
		String[] commands = {
				"dd if=/dev/urandom of=" + homeDir + "/random_seed bs=1 count=100000",
				"cat " + homeDir + "/random_seed " + homeDir + "/random_seed_orig " + homeDir + "/random_seed > " + homeDir + "/"
						+ output };
		Utils.runAsRoot(commands);
	}

	/**
	 * Launch Tcpdump on the device and save the trace in the folder app
	 *
	 * @param app
	 *            The folder to save trace
	 */
	public static void launchTcpdump(String app, String iface) {
		long now = new Date().getTime();
		String dir = traceBase + "/" + app;
		String[] commands = {
				"mkdir -p " + dir,
				"tcpdump -i " + iface + " -w " + dir + "/"
						+ app + "_" + now + ".pcap &"
					+ " echo $! > " + traceBase + "/tcpdump.pid" };
		Utils.runAsRoot(commands);
	}

	/**
	 * Kill the tcpdump process launched
	 */
	public static void killTcpdump() {
		String[] commands = {
			"kill `cat " + traceBase + "/tcpdump.pid`",
			"rm -f " + traceBase + "/tcpdump.pid" };
		Utils.runAsRoot(commands);
	}

	public static void killApp(UiAutomatorTestCase t, String appText) {
		t.getUiDevice().pressHome(); // if we're already in recent apps
		try {
			t.getUiDevice().pressRecentApps();
		} catch (RemoteException e) {
			e.printStackTrace();
			return;
		}
		t.sleep(1000);
		List<UiObject> available = getElems("com.android.systemui:id/recents_bg_protect", "com.android.systemui:id/app_label");
		for (UiObject uiObject : available) {
			try {
				if (uiObject.getText().equals(appText))
					swipe(uiObject, Orientation.RIGHT, 5);
			} catch (UiObjectNotFoundException e) {
				e.printStackTrace();
			}
		}
	}

	public static boolean openApp(UiAutomatorTestCase t, String appText,
			String packageName) throws UiObjectNotFoundException {
		// Wake up, kill app (if found) and pressHome before opening an app
		try {
			t.getUiDevice().wakeUp();
		} catch (RemoteException e1) { // not a big deal
			e1.printStackTrace();
		}
		killApp(t, appText);
		t.getUiDevice().pressHome();

		UiObject allAppsButton = new UiObject(
				new UiSelector().description("Apps"));

		allAppsButton.clickAndWaitForNewWindow();

		UiScrollable appViews = new UiScrollable(
				new UiSelector().scrollable(true));

		appViews.setAsHorizontalList();
		boolean succeed = false;
		UiObject settingsApp;
		int i = 0;
		while (!succeed) {
			try {
				settingsApp = appViews.getChildByText(new UiSelector()
						.className(android.widget.TextView.class.getName()),
						appText, false); // do not scroll, did in the catch
				succeed = true;
				settingsApp.clickAndWaitForNewWindow();
				}
			catch (UiObjectNotFoundException e) {
				if (i < 7)
					appViews.flingForward(); // move to one new panel each time
				else
					appViews.flingBackward();
			}
			i++;
		}

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

	public static UiObject getObjectWithDescription(String desc) {
		return new UiObject(new UiSelector().description(desc));
	}

	public static UiObject getObjectWithId(String id, int instance) {
		return new UiObject(new UiSelector().resourceId(id).instance(instance));
	}

	public static UiObject getObjectWithId(String id) {
		return getObjectWithId(id, 0);
	}

	public static UiObject getObjectWithClassName(String className, int instance) {
		return new UiObject(new UiSelector().className(className).instance(
				instance));
	}

	public static UiObject getObjectWithClassNameAndText(String className,
			String text) {
		return new UiObject(new UiSelector().className(className).text(text));
	}

	public static UiObject getObjectWithText(String text) {
		return new UiObject(new UiSelector().text(text));
	}

	public static UiScrollable getScrollableWithId(String id) {
		return new UiScrollable(new UiSelector().resourceId(id));
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

	public static boolean clickOnTheMiddle(UiAutomatorTestCase t) {
		return t.getUiDevice().click(t.getUiDevice().getDisplayWidth() / 2,
				t.getUiDevice().getDisplayHeight() / 2);
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

	public static boolean longClick(UiObject obj) {
		try {
			return obj.longClick();
		} catch (UiObjectNotFoundException e) {
			return false;
		}
	}

	public static boolean longClick(String id) {
		try {
			return longClick(getObject(id));
		} catch (UiObjectNotFoundException e) {
			return false;
		}
	}

	public static boolean swipe(String id, Orientation orientation, int steps) {
		try {
			return swipe(getObject(id), orientation, steps);
		} catch (UiObjectNotFoundException e) {
			return false;
		}
	}

	public static boolean swipe(UiObject obj, Orientation orientation, int steps) {
		try {
			switch (orientation) {
			case DOWN:
				return obj.swipeDown(steps);
			case UP:
				return obj.swipeUp(steps);
			case LEFT:
				return obj.swipeLeft(steps);
			case RIGHT:
				return obj.swipeRight(steps);
			default:
				return false;
			}
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
	
	public static boolean scrollForward(UiScrollable obj, int steps) {
		try {
			return obj.scrollForward(steps);
		} catch (UiObjectNotFoundException e) {
			return false;
		}
	}
	
	public static int getChildCount(UiObject obj) {
		try {
			return obj.getChildCount();
		} catch (UiObjectNotFoundException e) {
			return 0;
		}
	}
	
	public static boolean swipeLeft(UiObject obj, int steps) {
		try {
			return obj.swipeLeft(steps);
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
